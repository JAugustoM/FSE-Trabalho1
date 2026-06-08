# Arquivo: src/central/modbus.py

import struct
import threading
import time

import serial

from uart.funcs_aux import calcula_crc, processa_matricula

ADDR_ESTADO = 0x20
ADDR_CAMERAS = {1: 0x11, 2: 0x12, 3: 0x13, 4: 0x14}

MAX_TENTATIVAS = 3
TIMEOUT_CAMERA = 4.0


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
        self.night_mode = regs[10] if len(regs) > 10 else 0


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
        self._lock = threading.Lock()

    def _monta_leitura_custom(self, addr: int, start: int, count: int) -> bytearray:
        dados = struct.pack("<H", start) + struct.pack("<H", count)
        pacote = bytearray([addr, 0x03]) + bytearray(dados) + self.matricula
        return pacote + calcula_crc(pacote)

    def _monta_escrita_custom(
        self, addr: int, start: int, valores: list[int]
    ) -> bytearray:
        count = len(valores)
        cabecalho = struct.pack("<HHB", start, count, count * 2)
        dados = b"".join(struct.pack("<H", v) for v in valores)
        pacote = (
            bytearray([addr, 0x10])
            + bytearray(cabecalho)
            + bytearray(dados)
            + self.matricula
        )
        return pacote + calcula_crc(pacote)

    def _parse_leitura_custom(self, count: int) -> list[int] | None:
        header = self.ser.read(2)
        if len(header) < 2:
            return None

        if header[1] & 0x80:
            resto = self.ser.read(3)
            exc = resto[0] if resto else 0
            if exc != 0x02:
                print(
                    f"[MODBUS] Excecao de leitura no addr {header[0]:#04x}: codigo {exc:#04x}"
                )
            return None

        bytes_restantes = 1 + (count * 2) + 2
        payload_full = self.ser.read(bytes_restantes)
        raw = header + payload_full

        if len(raw) < (2 + bytes_restantes):
            return None

        if bytearray(raw[-2:]) != calcula_crc(raw[:-2]):
            return None

        return [
            struct.unpack(">H", raw[3 + i * 2 : 5 + i * 2])[0] for i in range(count)
        ]

    def _parse_escrita_custom(self) -> bool:
        header = self.ser.read(2)
        if len(header) < 2:
            return False

        if header[1] & 0x80:
            resto = self.ser.read(3)
            exc = resto[0] if resto else 0
            print(
                f"[MODBUS] Excecao na escrita addr {header[0]:#04x}: codigo {exc:#04x}"
            )
            return False

        payload = self.ser.read(6)
        raw = header + payload

        if len(raw) < 8:
            return False

        return bytearray(raw[-2:]) == calcula_crc(raw[:-2])

    def ler_registradores(self, addr: int, start: int, count: int) -> list[int] | None:
        with self._lock:
            time.sleep(0.05)
            for _ in range(MAX_TENTATIVAS):
                self.ser.reset_input_buffer()
                pacote = self._monta_leitura_custom(addr, start, count)
                self.ser.write(pacote)
                regs = self._parse_leitura_custom(count)
                if regs is not None:
                    return regs
            return None

    def escrever_registradores(self, addr: int, start: int, valores: list[int]) -> bool:
        with self._lock:
            time.sleep(0.05)
            for _ in range(MAX_TENTATIVAS):
                self.ser.reset_input_buffer()
                pacote = self._monta_escrita_custom(addr, start, valores)
                self.ser.write(pacote)
                if self._parse_escrita_custom():
                    return True
            print(
                f"[MODBUS] Falha ao escrever em {addr:#04x} apos esgotar alternativas."
            )
            return False

    def ler_estado_sistema(self) -> EstadoSistema | None:
        regs = self.ler_registradores(ADDR_ESTADO, 0, 11)
        if regs is None:
            return None
        return EstadoSistema(regs)

    def acionar_camera(self, sensor_id: int) -> ResultadoCamera | None:
        addr = ADDR_CAMERAS.get(sensor_id)
        if addr is None:
            print(f"[CAMERA] Sensor {sensor_id} sem camera associada")
            return None

        self.escrever_registradores(addr, 1, [0])
        time.sleep(0.1)

        if not self.escrever_registradores(addr, 1, [1]):
            print(f"[CAMERA] Falha ao disparar camera do sensor {sensor_id}")
            return None

        status_ok = False
        inicio = time.time()

        while time.time() - inicio < TIMEOUT_CAMERA:
            regs = self.ler_registradores(addr, 0, 1)

            if regs is not None:
                if regs[0] == 2:
                    status_ok = True
                    break
                if regs[0] == 3:  # 3 = Erro da câmera
                    print(
                        f"[CAMERA] Camera {sensor_id} retornou erro de processamento (Status=3)."
                    )
                    self.escrever_registradores(addr, 1, [0])
                    return None

            time.sleep(0.2)

        if not status_ok:
            print(f"[CAMERA] Timeout aguardando leitura da camera {sensor_id}")
            self.escrever_registradores(addr, 1, [0])
            return None

        regs = self.ler_registradores(addr, 2, 5)
        if regs is None:
            print(f"[CAMERA] Falha na leitura dos dados finais. Abortando.")
            self.escrever_registradores(addr, 1, [0])
            return None

        placa_bytes = b"".join(struct.pack(">H", r) for r in regs[:4])
        placa = placa_bytes.decode("ascii", errors="ignore").strip("\x00")
        confianca_bytes = regs[4]
        confianca = ((confianca_bytes & 0xFF00) >> 8) | (
            (confianca_bytes & 0x00FF) << 8
        )

        self.escrever_registradores(addr, 1, [0])

        print(
            f"[CAMERA] Sensor {sensor_id} disparada - Placa: {placa} | Confianca: {confianca}%"
        )
        return ResultadoCamera(placa, confianca)

    def fechar(self):
        self.ser.close()
