import time

import RPi.GPIO as GPIO


class HardwareController:
    def __init__(self, loop, config):
        self.loop = loop
        self.config = config
        self._estado_atual = None
        self._setup_gpio()

    @property
    def estado_atual(self):
        return self._estado_atual

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.config.sem_pins, GPIO.OUT, initial=GPIO.LOW)

        inputs = [
            self.config.btn_principal,
            self.config.btn_cruzamento,
            self.config.sensor1A,
            self.config.sensor1B,
            self.config.sensor2A,
            self.config.sensor2B,
        ]
        GPIO.setup(inputs, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def registrar_callbacks_botoes(self, callback_p, callback_c):
        GPIO.add_event_detect(
            self.config.btn_principal,
            GPIO.RISING,
            callback=lambda ch: self.loop.call_soon_threadsafe(callback_p),
            bouncetime=300,
        )
        GPIO.add_event_detect(
            self.config.btn_cruzamento,
            GPIO.RISING,
            callback=lambda ch: self.loop.call_soon_threadsafe(callback_c),
            bouncetime=300,
        )

    def registrar_callbacks_sensores(
        self, callback_s1A, callback_s1B, callback_s2A, callback_s2B
    ):
        def wrap_s1_a(ch):
            self.loop.call_soon_threadsafe(callback_s1A, time.perf_counter())

        def wrap_s1_b(ch):
            self.loop.call_soon_threadsafe(callback_s1B, time.perf_counter())

        def wrap_s2_a(ch):
            self.loop.call_soon_threadsafe(callback_s2A, time.perf_counter())

        def wrap_s2_b(ch):
            self.loop.call_soon_threadsafe(callback_s2B, time.perf_counter())

        GPIO.add_event_detect(
            self.config.sensor1A,
            GPIO.RISING,
            callback=wrap_s1_a,
        )
        GPIO.add_event_detect(
            self.config.sensor1B,
            GPIO.RISING,
            callback=wrap_s1_b,
        )
        GPIO.add_event_detect(
            self.config.sensor2A,
            GPIO.RISING,
            callback=wrap_s2_a,
        )
        GPIO.add_event_detect(
            self.config.sensor2B,
            GPIO.RISING,
            callback=wrap_s2_b,
        )

    def enviar_codigo_3bits(self, estado):
        self._estado_atual = estado
        b0 = estado & 1
        b1 = (estado >> 1) & 1
        b2 = (estado >> 2) & 1
        GPIO.output(self.config.sem_pins, [b0, b1, b2])
