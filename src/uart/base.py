import struct
from time import sleep

import serial
from serial.serialutil import SerialTimeoutException


class ProtocoloBase:
    def __init__(self, port: str = "/dev/ttyS0"):
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
        )

    def comandoLeitura(self, cmd: int, matricula: int) -> int | float | str | None:
        bytes_matricula = [int(digito) for digito in str(matricula)]

        if len(bytes_matricula) != 6:
            print("[ERRO] Matrícula inválida")
            return

        recebido: bytes
        resultado: int | float | str = ""

        try:
            self.ser.write(bytearray([cmd + 0xA0] + bytes_matricula))
            print("[OK] Comando de Leitura Enviado")

            sleep(0.25)

            match cmd:
                case 1:
                    recebido = self.ser.read(4)
                    if len(recebido) > 0:
                        resultado = int.from_bytes(recebido, "little")
                case 2:
                    recebido = self.ser.read(4)
                    if len(recebido) > 0:
                        resultado = struct.unpack("<f", recebido)[0]
                case _:
                    tamanho = self.ser.read(1)
                    if len(tamanho) > 0:
                        recebido = self.ser.read(int.from_bytes(tamanho, "little"))
                        resultado = recebido.decode("utf-8")

            print(f"[OK] Mensagem recebida: {resultado}")
            return resultado
        except serial.SerialTimeoutException:
            print("[ERRO] Timeout Detectado")

    def finalizar(self):
        self.ser.close()
