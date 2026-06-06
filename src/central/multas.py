import os
from dataclasses import dataclass
from datetime import datetime

ARQUIVO_MULTAS = "multas.log"
VALOR_MULTA = 293.47


@dataclass
class Multa:
    timestamp: str
    cruzamento: int
    sensor_id: int
    velocidade_kmh: float
    camera_modbus: int
    placa: str
    confianca: int
    valor: float


class LogMultas:
    def __init__(self, arquivo: str = ARQUIVO_MULTAS):
        self.arquivo = arquivo
        self.multas: list[Multa] = []
        self._carregar()

    def _carregar(self):
        if not os.path.exists(self.arquivo):
            return
        with open(self.arquivo) as f:
            for linha in f:
                if linha.startswith("timestamp"):
                    continue
                partes = [p.strip() for p in linha.split("|")]
                if len(partes) < 8:
                    continue
                try:
                    self.multas.append(Multa(
                        timestamp=partes[0],
                        cruzamento=int(partes[1]),
                        sensor_id=int(partes[2]),
                        velocidade_kmh=float(partes[3]),
                        camera_modbus=int(partes[4], 16),
                        placa=partes[5],
                        confianca=int(partes[6]),
                        valor=float(partes[7]),
                    ))
                except ValueError:
                    pass

    def registrar(self, cruzamento, sensor_id, velocidade_kmh, camera_modbus, placa, confianca) -> Multa:
        multa = Multa(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            cruzamento=cruzamento,
            sensor_id=sensor_id,
            velocidade_kmh=round(velocidade_kmh, 1),
            camera_modbus=camera_modbus,
            placa=placa,
            confianca=confianca,
            valor=VALOR_MULTA,
        )
        self.multas.append(multa)

        escrever_cabecalho = not os.path.exists(self.arquivo)
        with open(self.arquivo, "a") as f:
            if escrever_cabecalho:
                f.write("timestamp | cruzamento | sensor | velocidade (km/h) | câmera MODBUS | placa | confiança (%) | Valor da Multa\n")
            f.write(
                f"{multa.timestamp} | {multa.cruzamento} | {multa.sensor_id} | "
                f"{multa.velocidade_kmh} | {multa.camera_modbus:#04x} | {multa.placa} | "
                f"{multa.confianca} | R$ {multa.valor:.2f}\n"
            )

        print(f"[MULTA] Placa {placa} | {velocidade_kmh:.0f} km/h | Câmera {camera_modbus:#04x} | R$ {VALOR_MULTA:.2f}")
        return multa
