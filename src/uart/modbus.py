from typing import Any

from .base import ProtocoloBase
from .funcs_aux import monta_pacote, processa_matricula, recebe_pacote_modbus

ENDERECO = 0x01
COD_LEITURA = 0x23
COD_ENVIO = 0x16


class ProtocoloMODBUS(ProtocoloBase):
    def comandoLeitura(self, cmd: int, matricula: str) -> Any | None:
        matricula_bytes = processa_matricula(matricula)
        if not matricula_bytes:
            return None

        sub_cod = cmd + 0xA0
        pacote = monta_pacote(ENDERECO, COD_LEITURA, sub_cod, None, matricula_bytes, True)

        self.ser.write(pacote)
        print(f"[MODBUS] Comando de Leitura {hex(sub_cod)}. Bytes: {pacote.hex(' ')}")

        (_, resultado) = recebe_pacote_modbus(cmd, self.ser)
        return resultado

    def comandoEnvio(self, cmd: int, dados: Any, matricula: str) -> Any | None:
        matricula_bytes = processa_matricula(matricula)
        if not matricula_bytes:
            return None

        sub_cod = cmd + 0xB0
        pacote = monta_pacote(ENDERECO, COD_ENVIO, sub_cod, dados, matricula_bytes, True)

        self.ser.write(pacote)
        print(f"[MODBUS] Comando de Envio {hex(sub_cod)}. Bytes: {pacote.hex(' ')}")

        (_, resultado) = recebe_pacote_modbus(cmd, self.ser)
        return resultado
