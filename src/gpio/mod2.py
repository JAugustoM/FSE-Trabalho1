from time import sleep, time

import RPi.GPIO as GPIO

from .setup import BOTC_M2, BOTP_M2, SEM0, SEM1, SEM2


class SemaforoCruzamento:
    def __init__(self):
        self.pedido_ped_prin = False
        self.pedido_ped_cruz = False
        self._estado_atual = None
        self._configurar_interrupcoes()

    def _configurar_interrupcoes(self):
        GPIO.add_event_detect(
            BOTP_M2, GPIO.RISING, callback=self._btn_principal_callback, bouncetime=300
        )
        GPIO.add_event_detect(
            BOTC_M2, GPIO.RISING, callback=self._btn_cruzamento_callback, bouncetime=300
        )

    def _btn_principal_callback(self, channel):
        print("\n[M2] Botão Pedestre Principal pressionado!")
        if self._estado_atual == 1:
            self.pedido_ped_prin = True

    def _btn_cruzamento_callback(self, channel):
        print("\n[M2] Botão Pedestre Cruzamento pressionado!")
        if self._estado_atual == 5:
            self.pedido_ped_cruz = True

    def enviar_codigo_3bits(self, estado):
        """Converte o estado (número inteiro) em 3 bits e envia para os pinos GPIO."""
        self._estado_atual = estado
        b0 = estado & 1
        b1 = (estado >> 1) & 1
        b2 = (estado >> 2) & 1

        GPIO.output([SEM0, SEM1, SEM2], [b0, b1, b2])

        print(f"\n[M2] ESTADO ATUAL: {estado} (Bits: {b2}{b1}{b0}) ---")

    def esperar_tempo_variavel(self, tempo_maximo, checar_pedido):
        """
        Espera até o tempo_maximo, mas é interrompido imediatamente se
        a função checar_pedido() retornar True.
        """
        inicio = time()
        while (time() - inicio) < tempo_maximo:
            if checar_pedido():
                print("[M2] Sinal verde interrompido pelo pedestre!")
                break
            sleep(0.1)

    def executar_ciclo(self):
        while True:
            # ESTADO 1 (Verde Principal / Vermelho Cruzamento)
            self.pedido_ped_prin = False
            self.enviar_codigo_3bits(1)
            print("[M2] Via Principal: VERDE | Via Cruzamento: VERMELHO")
            sleep(10)
            self.esperar_tempo_variavel(10, lambda: self.pedido_ped_prin)

            # ESTADO 2 (Amarelo Principal)
            self.enviar_codigo_3bits(2)
            print("[M2] Via Principal: AMARELO | Via Cruzamento: VERMELHO")
            sleep(2)

            # ESTADO 4 (Vermelho Total)
            self.enviar_codigo_3bits(4)
            print("[M2] Via Principal: VERMELHO | Via Cruzamento: VERMELHO")
            sleep(2)

            # ESTADO 5 (Vermelho Principal / Verde Cruzamento)
            self.pedido_ped_cruz = False
            self.enviar_codigo_3bits(5)
            print("[M2] Via Principal: VERMELHO | Via Cruzamento: VERDE")
            sleep(5)
            self.esperar_tempo_variavel(5, lambda: self.pedido_ped_cruz)

            # ESTADO 6 (Amarelo Cruzamento)
            self.enviar_codigo_3bits(6)
            print("[M2] Via Principal: VERMELHO | Via Cruzamento: AMARELO")
            sleep(2)

            # ESTADO 4 (Vermelho Total)
            self.enviar_codigo_3bits(4)
            print("[M2] Via Principal: VERMELHO | Via Cruzamento: VERMELHO")
            sleep(2)
