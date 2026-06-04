import asyncio
import json

from .modos import Modo


class TCPClient:
    def __init__(self, config, semaforo, sensores):
        self.host = config.server_host
        self.port = config.server_port
        self.cruzamento_id = config.id
        self.semaforo = semaforo
        self.sensores = sensores
        self.reader = None
        self.writer = None

    async def connect(self):
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port
                )
                print(f"[TCP] Conectado ao Servidor Central em {self.host}:{self.port}")
                return
            except Exception as e:
                print("[TCP] Falha na conexão. Retentando em 5s...")
                await asyncio.sleep(5)

    async def le_comandos(self):
        """Aguarda ordens (Modo Noturno, Emergência) do Servidor Central"""
        while True:
            if not self.reader:
                await asyncio.sleep(1)
                continue

            try:
                data = await self.reader.readline()
                if not data:
                    print("[TCP] Conexão perdida. Reconectando...")
                    self.reader = None
                    await self.connect()
                    continue

                payload = json.loads(data.decode().strip())
                comando = payload.get("comando")

                if comando == "noturno":
                    self.semaforo.modo = Modo.NOITE
                elif comando == "emergencia_principal":
                    self.semaforo.modo = Modo.EMERGENCIA_PRINCIPAL
                elif comando == "emergencia_cruzamento":
                    self.semaforo.modo = Modo.EMERGENCIA_CRUZAMENTO
                elif comando == "normal":
                    self.semaforo.modo = Modo.NORMAL

            except Exception as e:
                print(f"[TCP] Erro no listener: {e}")

    async def loop_telemetria(self):
        """Envia contagem de veículos a cada 2 segundos"""
        while True:
            await asyncio.sleep(2)
            if not self.writer:
                continue

            s1_count, s2_count = self.sensores.reset_counts()
            msg = {
                "tipo": "telemetria",
                "cruzamento": self.cruzamento_id,
                "sensor_1_count": s1_count,
                "sensor_2_count": s2_count,
            }
            self.writer.write((json.dumps(msg) + "\n").encode())
            await self.writer.drain()

    async def loop_alerta(self):
        """Consome a fila de alertas (>60km/h) e envia imediatamente"""
        while True:
            alerta = await self.sensores.alert_queue.get()
            if self.writer:
                self.writer.write((json.dumps(alerta) + "\n").encode())
                await self.writer.drain()
