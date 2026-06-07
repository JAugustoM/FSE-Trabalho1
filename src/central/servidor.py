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
        self.historico_sensores = {}

        self.tcp.on("telemetria", self._handle_telemetria)
        self.tcp.on("infracao", self._handle_infracao)

    def _handle_telemetria(self, msg: dict):
        cruzamento = msg["cruzamento"]
        now = time.time()

        s1_count = msg.get("sensor_1_count", 0)
        s1_speed = msg.get("sensor_1_avg_speed", 0.0)
        s2_count = msg.get("sensor_2_count", 0)
        s2_speed = msg.get("sensor_2_avg_speed", 0.0)

        g_s1 = str((cruzamento - 1) * 2 + 1)
        g_s2 = str((cruzamento - 1) * 2 + 2)

        if g_s1 not in self.historico_sensores:
            self.historico_sensores[g_s1] = []
        if g_s2 not in self.historico_sensores:
            self.historico_sensores[g_s2] = []

        self.historico_sensores[g_s1].append((now, s1_count, s1_speed))
        self.historico_sensores[g_s2].append((now, s2_count, s2_speed))

        for g_id in [g_s1, g_s2]:
            self.historico_sensores[g_id] = [
                x for x in self.historico_sensores[g_id] if now - x[0] <= 60
            ]

        sensores_atualizados = {}
        for g_id in [g_s1, g_s2]:
            hist = self.historico_sensores[g_id]
            fluxo_minuto = sum(x[1] for x in hist)

            total_carros_vel = sum(x[1] for x in hist if x[2] > 0)
            vel_media = (
                sum(x[2] * x[1] for x in hist if x[2] > 0) / total_carros_vel
                if total_carros_vel > 0
                else 0.0
            )

            sensores_atualizados[g_id] = {
                "fluxo": fluxo_minuto,
                "vel_media": round(vel_media, 1),
            }

        self.estado.atualizar_dados_sensores(sensores_atualizados)

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
        noturno_anterior = self.estado.dados["modo_noturno"]

        while True:
            try:
                estado = self.modbus.ler_estado_sistema()
                if estado is None:
                    time.sleep(0.3)
                    continue

                modo_noturno_atual = estado.night_mode == 1
                if modo_noturno_atual != noturno_anterior:
                    noturno_anterior = modo_noturno_atual
                    self.estado.dados["modo_noturno"] = modo_noturno_atual
                    self.estado.salvar()
                    self.tcp.broadcast(
                        {"comando": "noturno" if modo_noturno_atual else "normal"}
                    )
                    print(
                        f"[MODBUS] Modo noturno alterado via hardware para: {'ATIVO' if modo_noturno_atual else 'INATIVO'}"
                    )

                if estado.active and not emergencia_anterior:
                    emergencia_anterior = True
                    self.estado.dados["emergencia_ativa"] = True
                    self.estado.salvar()
                    self._handle_emergencia(estado)

                elif not estado.active and emergencia_anterior:
                    emergencia_anterior = False
                    self.estado.dados["emergencia_ativa"] = False
                    self.estado.salvar()
                    if self.estado.dados["modo_noturno"]:
                        self.tcp.broadcast({"comando": "noturno"})
                    else:
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
