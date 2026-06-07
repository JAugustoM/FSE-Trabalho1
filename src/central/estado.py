import json
import os
from threading import Lock

ARQUIVO_ESTADO = "estado_central.json"


class EstadoPersistente:
    def __init__(self, arquivo: str = ARQUIVO_ESTADO):
        self.arquivo = arquivo
        self._lock = Lock()
        self.dados = {
            "modo_noturno": False,
            "emergencia_ativa": False,
            "sensores": {},
        }
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.arquivo):
            with open(self.arquivo) as f:
                try:
                    self.dados.update(json.load(f))
                except json.JSONDecodeError:
                    pass

    def salvar(self):
        with self._lock:
            with open(self.arquivo, "w") as f:
                json.dump(self.dados, f, indent=2)

    def atualizar_dados_sensores(self, sensores_dados: dict):
        with self._lock:
            for s_id, info in sensores_dados.items():
                self.dados["sensores"][str(s_id)] = info
        self.salvar()
