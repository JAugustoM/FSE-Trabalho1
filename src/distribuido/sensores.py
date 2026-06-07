import asyncio
import time


class SensorManager:
    def __init__(self, loop, hardware, cruzamento_id):
        self.hardware = hardware
        self.cruzamento_id = cruzamento_id

        self.estado_s1 = {"tempo_a": [], "count": 0, "velocidades": []}
        self.estado_s2 = {"tempo_a": [], "count": 0, "velocidades": []}

        self.alert_queue = asyncio.Queue()

        self.hardware.registrar_callbacks_sensores(
            self._sensor1A, self._sensor1B, self._sensor2A, self._sensor2B
        )

    def _processar_passagem(self, estado_sensor, sensor_id, tempo_b):
        if not estado_sensor["tempo_a"]:
            return

        tempo_a = estado_sensor["tempo_a"].pop(0)

        dt_bruto = tempo_b - tempo_a
        CALIBRACAO_S = 0.0413
        dt = dt_bruto - CALIBRACAO_S

        estado_sensor["count"] += 1

        if 0 < dt < 2.0:
            velocidade_kmh = (2.0 / dt) * 3.6
            estado_sensor["velocidades"].append(velocidade_kmh)
            print(
                f"[Sensor {sensor_id}] Veículo detectado! v={velocidade_kmh:.1f} km/h"
            )

            if velocidade_kmh > 60.0:
                print(
                    f"!!! INFRAÇÃO: Veículo a {velocidade_kmh:.1f} km/h no Sensor {sensor_id} !!!"
                )
                alerta = {
                    "tipo": "infracao",
                    "cruzamento": self.cruzamento_id,
                    "sensor_id": sensor_id,
                    "velocidade_kmh": round(velocidade_kmh, 2),
                    "timestamp": tempo_b,
                }
                self.alert_queue.put_nowait(alerta)

    def _sensor1A(self, tempo_a):
        self.estado_s1["tempo_a"].append(tempo_a)

    def _sensor1B(self, tempo_b):
        self._processar_passagem(
            self.estado_s1, 1 + 2 * (self.cruzamento_id - 1), tempo_b
        )

    def _sensor2A(self, tempo_a):
        self.estado_s2["tempo_a"].append(tempo_a)

    def _sensor2B(self, tempo_b):
        self._processar_passagem(
            self.estado_s2, 2 + 2 * (self.cruzamento_id - 1), tempo_b
        )

    def reset_counts(self):
        s1 = self.estado_s1["count"]
        s2 = self.estado_s2["count"]

        s1_speed = (
            sum(self.estado_s1["velocidades"]) / len(self.estado_s1["velocidades"])
            if self.estado_s1["velocidades"]
            else 0.0
        )
        s2_speed = (
            sum(self.estado_s2["velocidades"]) / len(self.estado_s2["velocidades"])
            if self.estado_s2["velocidades"]
            else 0.0
        )

        self.estado_s1["count"] = 0
        self.estado_s1["velocidades"] = []
        self.estado_s2["count"] = 0
        self.estado_s2["velocidades"] = []

        return s1, s1_speed, s2, s2_speed
