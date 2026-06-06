import struct
import time

import serial

from uart.funcs_aux import calcula_crc, processa_matricula

ADDR_ESTADO = 0x20
ADDR_CAMERAS = {1: 0x11, 2: 0x12, 3: 0x13, 4: 0x14}

MAX_TENTATIVAS = 3
TIMEOUT_CAMERA = 2.0


class EstadoSistema:
    def __init__(self, regs: list[int]):
        self.active = regs[0]
        self.road = regs[1]
        self.direction = regs[2]
        self.intersection_id = regs[3]
        self.vehicle_type = regs[4]
        self.signal_group = regs[5]
        self.timed_out = regs[6]
        self.unattended_count = regs[7]
        self.elapsed_s = regs[8] / 10
        self.max_time_s = regs[9] / 10


class ResultadoCamera:
    def __init__(self, placa: str, confianca: int):
        self.placa = placa
        self.confianca = confianca


class ModbusClient:
    def __init__(self, port: str = "/dev/serial0", matricula: str = "041099"):
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
        )
        self.matricula = processa_matricula(matricula)

    def _monta_leitura(self, addr: int, start: int, count: int) -> bytearray:
        dados = struct.pack(">H", start) + struct.pack("<H", count)
        pacote = bytearray([addr, 0x03]) + bytearray(dados) + self.matricula
        return pacote + calcula_crc(pacote)

    def _monta_escrita(self, addr: int, start: int, valores: list[int]) -> bytearray:
        count = len(valores)
        cabecalho = struct.pack(">HHB", start, count, count * 2)
        dados = b"".join(struct.pack(">H", v) for v in valores)
        pacote = bytearray([addr, 0x10]) + bytearray(cabecalho) + bytearray(dados) + self.matricula
        return pacote + calcula_crc(pacote)

    def _parse_leitura(self, count: int) -> list[int] | None:
        n_total = 2 + 1 + count * 2 + 2

        header = self.ser.read(2)
        if len(header) < 2:
            return None

        if header[1] & 0x80:
            resto = self.ser.read(3)
            exc = resto[0] if resto else 0
            if exc != 0x02:
                print(f"[MODBUS] Excecao {header[0]:#04x}: codigo {exc:#04x}")
            return None

        payload = self.ser.read(n_total - 2)
        raw = header + payload
        if len(raw) < n_total:
            return None

        if bytearray(raw[-2:]) != calcula_crc(raw[:-2]):
            return None

        return [
            struct.unpack(">H", raw[3 + i * 2: 5 + i * 2])[0]
            for i in range(count)
        ]

    def _parse_escrita(self) -> bool:
        header = self.ser.read(2)
        if len(header) < 2:
            return False

        if header[1] & 0x80:
            resto = self.ser.read(3)
            exc = resto[0] if resto else 0
            print(f"[MODBUS] Excecao na escrita {header[0]:#04x}: codigo {exc:#04x}")
            return False

        payload = self.ser.read(6)
        raw = header + payload
        if len(raw) < 8:
            return False

        return bytearray(raw[-2:]) == calcula_crc(raw[:-2])

    def ler_registradores(self, addr: int, start: int, count: int) -> list[int] | None:
        for _ in range(MAX_TENTATIVAS):
            self.ser.reset_input_buffer()
            self.ser.write(self._monta_leitura(addr, start, count))
            regs = self._parse_leitura(count)
            if regs is not None:
                return regs
        return None

    def escrever_registradores(self, addr: int, start: int, valores: list[int]) -> bool:
        for _ in range(MAX_TENTATIVAS):
            self.ser.reset_input_buffer()
            self.ser.write(self._monta_escrita(addr, start, valores))
            if self._parse_escrita():
                return True
        print(f"[MODBUS] Falha ao escrever em {addr:#04x} apos {MAX_TENTATIVAS} tentativas")
        return False

    def ler_estado_sistema(self) -> EstadoSistema:
        regs = self.ler_registradores(ADDR_ESTADO, 0, 10)
        if regs is None:
            regs = [0] * 10
        return EstadoSistema(regs)

    def acionar_camera(self, sensor_id: int) -> ResultadoCamera | None:
        addr = ADDR_CAMERAS.get(sensor_id)
        if addr is None:
            print(f"[CAMERA] Sensor {sensor_id} sem camera associada")
            return None

        if not self.escrever_registradores(addr, 1, [1]):
            print(f"[CAMERA] Falha ao disparar camera do sensor {sensor_id}")
            return None

        status_ok = False
        inicio = time.time()
        while time.time() - inicio < TIMEOUT_CAMERA:
            regs = self.ler_registradores(addr, 0, 1)
            if regs is None:
                break
            if regs[0] == 2:
                status_ok = True
                break
            if regs[0] == 3:
                print(f"[CAMERA] Camera {sensor_id} retornou erro de captura")
                self.escrever_registradores(addr, 1, [0])
                return None
            time.sleep(0.1)

        if not status_ok:
            print(f"[CAMERA] Timeout aguardando camera {sensor_id}")
            self.escrever_registradores(addr, 1, [0])
            return None

        regs = self.ler_registradores(addr, 2, 5)
        if regs is None:
            self.escrever_registradores(addr, 1, [0])
            return None

        placa = "".join(
            chr((r >> 8) & 0xFF) + chr(r & 0xFF) for r in regs[:4]
        ).strip("\x00")
        confianca = regs[4]

        self.escrever_registradores(addr, 1, [0])

        print(f"[CAMERA] Sensor {sensor_id} - Placa: {placa} | Confianca: {confianca}%")
        return ResultadoCamera(placa, confianca)

    def fechar(self):
        self.ser.close()
