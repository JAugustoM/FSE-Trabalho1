import threading
from time import sleep, time

import RPi.GPIO as GPIO

from .setup import BOTC_M1, BOTP_M1, LED0, LED1, LED2


class SemaforoLEDs:
    TEMPO_MIN_VERDE = 5
    TEMPO_VERDE = 10
    TEMPO_AMARELO = 2
    TEMPO_VERMELHO = 10

    def __init__(self):
        self._estado = None
        self.pedido_pedestre = False
        self._configurar_interrupcoes()

    def _configurar_interrupcoes(self):
        GPIO.add_event_detect(
            BOTP_M1, GPIO.RISING, callback=self._btn_principal_callback, bouncetime=300
        )
        GPIO.add_event_detect(
            BOTC_M1, GPIO.RISING, callback=self._btn_cruzamento_callback, bouncetime=300
        )

    def _btn_principal_callback(self, channel):
        print("[M1] Botão Pedestre Principal pressionado!")
        if self._estado == "verde":
            self.pedido_pedestre = True

    def _btn_cruzamento_callback(self, channel):
        print("[M1] Botão Pedestre Cruzamento pressionado!")
        if self._estado == "verde":
            self.pedido_pedestre = True

    def _set_leds(self, verde, amarelo, vermelho):
        GPIO.output(LED0, verde)
        GPIO.output(LED1, amarelo)
        GPIO.output(LED2, vermelho)

    def _esperar_interrompivel(self, duracao):
        inicio = time()
        while (time() - inicio) < duracao:
            if self.pedido_pedestre:
                return
            sleep(0.05)

    def executar_ciclo(self):
        while True:
            self._estado = "verde"
            self.pedido_pedestre = False
            self._set_leds(GPIO.HIGH, GPIO.LOW, GPIO.LOW)
            print("[M1] Verde")
            sleep(self.TEMPO_MIN_VERDE)
            self._esperar_interrompivel(self.TEMPO_VERDE - self.TEMPO_MIN_VERDE)

            self._estado = "amarelo"
            self._set_leds(GPIO.LOW, GPIO.HIGH, GPIO.LOW)
            print("[M1] Amarelo")
            sleep(self.TEMPO_AMARELO)

            self._estado = "vermelho"
            self._set_leds(GPIO.LOW, GPIO.LOW, GPIO.HIGH)
            print("[M1] Vermelho")
            sleep(self.TEMPO_VERMELHO)
