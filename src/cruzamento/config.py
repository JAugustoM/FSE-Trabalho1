from dataclasses import dataclass
from typing import Tuple


@dataclass
class CruzamentoConfig:
    id: int
    sem_pins: Tuple[int, int, int]
    btn_principal: int
    btn_cruzamento: int
    sensor1A: int
    sensor1B: int
    sensor2A: int
    sensor2B: int
    server_host: str = "127.0.0.1"
    server_port: int = 5000


def get_config(cruzamento_id: int) -> CruzamentoConfig:
    if cruzamento_id == 1:
        return CruzamentoConfig(
            id=1,
            sem_pins=(17, 18, 23),
            btn_principal=1,
            btn_cruzamento=12,
            sensor1A=16,
            sensor1B=20,
            sensor2A=21,
            sensor2B=27,
        )
    elif cruzamento_id == 2:
        return CruzamentoConfig(
            id=2,
            sem_pins=(24, 8, 7),
            btn_principal=25,
            btn_cruzamento=22,
            sensor1A=11,
            sensor1B=0,
            sensor2A=5,
            sensor2B=6,
        )
    raise ValueError("ID de cruzamento inválido. Deve ser 1 ou 2.")
