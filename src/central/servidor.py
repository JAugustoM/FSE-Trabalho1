import threading
import time

from .estado import EstadoPersistente
from .interface import Interface
from .modbus import ModbusClient
from .multas import LogMultas
from .tcp_server import TCPServer


class ServidorCentral:
    def __init__(
        self,
        porta_tcp: int = 5000,
        porta_serial: str = "/dev/serial0",
        matricula: str = "041099",
    ):
        self.modbus = ModbusClient(port=porta_serial, matricula=matricula)
        self.tcp = TCPServer(porta=porta_tcp)
        self.log_multas = LogMultas()
        self.estado = EstadoPersistente()
        self.interface = Interface(self)

        self.tcp.on("telemetria", self._handle_telemetria)
        self.tcp.on("infracao", self._handle_infracao)

    def _handle_telemetria(self, msg: dict):
        sensores = {
            1: msg.get("sensor_1_count", 0),
            2: msg.get("sensor_2_count", 0),
        }
        self.estado.atualizar_contagem(msg["cruzamento"], sensores)

    def _handle_infracao(self, msg: dict):
        cruzamento = msg["cruzamento"]
        sensor_id = msg["sensor_id"]
        velocidade = msg["velocidade_kmh"]

        print(f"\n[INFRACAO] C{cruzamento} S{sensor_id}: {velocidade:.1f} km/h")

        resultado = self.modbus.acionar_camera(sensor_id)
        if resultado:
            self.log_multas.registrar(
                cruzamento=cruzamento,
                sensor_id=sensor_id,
                velocidade_kmh=velocidade,
                camera_modbus=0x10 + sensor_id,
                placa=resultado.placa,
                confianca=resultado.confianca,
            )

    def _loop_modbus(self):
        emergencia_anterior = False

        while True:
            try:
                estado = self.modbus.ler_estado_sistema()

                if estado.active and not emergencia_anterior:
                    emergencia_anterior = True
                    self.estado.dados["emergencia_ativa"] = True
                    self.estado.salvar()
                    self._handle_emergencia(estado)

                elif not estado.active and emergencia_anterior:
                    emergencia_anterior = False
                    self.estado.dados["emergencia_ativa"] = False
                    self.estado.salvar()
                    self.tcp.broadcast({"comando": "normal"})
                    print("[MODBUS] Emergência encerrada — ciclo normal retomado")

            except Exception as e:
                print(f"[MODBUS] Erro no loop: {e}")
                time.sleep(2)
                continue

            time.sleep(0.3)

    def _handle_emergencia(self, estado):
        print(
            f"[MODBUS] Emergência detectada! "
            f"road={estado.road} direction={estado.direction} "
            f"intersection={estado.intersection_id} signal_group={estado.signal_group}"
        )

        if estado.signal_group == 1:
            comando = "emergencia_principal"
        else:
            comando = "emergencia_cruzamento"

        msg = {"comando": comando}

        if estado.intersection_id == 0:
            self.tcp.broadcast(msg)
        else:
            self.tcp.enviar(estado.intersection_id, msg)

    def iniciar(self):
        self.tcp.iniciar()
        threading.Thread(target=self._loop_modbus, daemon=True).start()

        if self.estado.dados["modo_noturno"]:
            self.tcp.broadcast({"comando": "noturno"})

        self.interface.executar()

    def parar(self):
        self.tcp.parar()
        self.modbus.fechar()
