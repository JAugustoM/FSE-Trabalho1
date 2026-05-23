from typing import Any

import serial

from .funcs_aux import monta_pacote, processa_matricula, recebe_pacote


class ProtocoloBase:
    def __init__(self, port: str = "/dev/serial0"):
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
        )

    def comandoLeitura(self, cmd: int, matricula: str) -> Any | None:
        matricula_bytes = processa_matricula(matricula)
        if not matricula_bytes:
            return None

        cmd_byte = cmd + 0xA0
        pacote = monta_pacote(None, None, cmd_byte, None, matricula_bytes, False)

        self.ser.write(pacote)
        print(f"[OK] Comando de Leitura {hex(cmd_byte)}. Bytes: {pacote.hex(' ')}")

        (_, resultado) = recebe_pacote(cmd, self.ser)

        return resultado

    def comandoEnvio(self, cmd: int, dados: Any, matricula: str) -> Any | None:
        bytes_matricula = processa_matricula(matricula)
        if not bytes_matricula:
            return None

        cmd_byte = cmd + 0xB0
        pacote = monta_pacote(None, None, cmd_byte, dados, bytes_matricula, False)

        self.ser.write(pacote)
        print(f"[OK] Comando de Envio {hex(cmd_byte)}. Bytes: {pacote.hex(' ')}")

        (_, resultado) = recebe_pacote(cmd, self.ser)

        return resultado

    def finalizar(self):
        self.ser.close()
