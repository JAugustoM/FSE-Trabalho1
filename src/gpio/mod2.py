import threading
from time import sleep, time

import RPi.GPIO as GPIO

from .setup import BOTC_M2, BOTP_M2, SEM0, SEM1, SEM2


class SemaforoCruzamento:
    def __init__(self):
        self.pedido_ped_prin = False
        self.pedido_ped_cruz = False

        self.thread_monitoramento = threading.Thread(
            target=self.monitorar_botoes, daemon=True
        )
        self.thread_monitoramento.start()

    def monitorar_botoes(self):
        estado_anterior_prin = GPIO.LOW
        estado_anterior_cruz = GPIO.LOW

        while True:
            estado_atual_prin = GPIO.input(BOTP_M2)
            estado_atual_cruz = GPIO.input(BOTC_M2)

            if estado_atual_prin == GPIO.HIGH and estado_anterior_prin == GPIO.LOW:
                print("\n[!] Botão Pedestre Principal pressionado!")
                self.pedido_ped_prin = True

            if estado_atual_cruz == GPIO.HIGH and estado_anterior_cruz == GPIO.LOW:
                print("\n[!] Botão Pedestre Cruzamento pressionado!")
                self.pedido_ped_cruz = True

            estado_anterior_prin = estado_atual_prin
            estado_anterior_cruz = estado_atual_cruz

            sleep(0.2)

    def enviar_codigo_3bits(self, estado):
        """Converte o estado (número inteiro) em 3 bits e envia para os pinos GPIO."""
        b0 = estado & 1
        b1 = (estado >> 1) & 1
        b2 = (estado >> 2) & 1

        GPIO.output([SEM0, SEM1, SEM2], [b0, b1, b2])

        print(f"\n--- ESTADO ATUAL: {estado} (Bits: {b2}{b1}{b0}) ---")

    def esperar_tempo_variavel(self, tempo_maximo, checar_pedido):
        """
        Espera até o tempo_maximo, mas é interrompido imediatamente se
        a função checar_pedido() retornar True.
        """
        inicio = time()
        while (time() - inicio) < tempo_maximo:
            if checar_pedido():
                print(" -> Sinal verde interrompido pelo pedestre!")
                break
            sleep(0.1)

    def executar_ciclo(self):
        while True:
            # ESTADO 1 (Verde Principal / Vermelho Cruzamento)
            self.enviar_codigo_3bits(1)
            self.pedido_ped_cruz = False
            print("Via Principal: VERDE | Via Cruzamento: VERMELHO")
            sleep(10)
            self.esperar_tempo_variavel(10, lambda: self.pedido_ped_prin)

            # ESTADO 2 (Amarelo Principal)
            self.enviar_codigo_3bits(2)
            print("Via Principal: AMARELO | Via Cruzamento: VERMELHO")
            sleep(2)

            # ESTADO 4 (Vermelho Total)
            self.enviar_codigo_3bits(4)
            print("Via Principal: VERMELHO | Via Cruzamento: VERMELHO")
            sleep(2)

            # ESTADO 5 (Vermelho Principal / Verde Cruzamento)
            self.enviar_codigo_3bits(5)
            self.pedido_ped_prin = False
            print("Via Principal: VERMELHO | Via Cruzamento: VERDE")
            sleep(5)
            self.esperar_tempo_variavel(5, lambda: self.pedido_ped_cruz)

            # ESTADO 6 (Amarelo Cruzamento)
            self.enviar_codigo_3bits(6)
            print("Via Principal: VERMELHO | Via Cruzamento: AMARELO")
            sleep(2)

            # ESTADO 4 (Vermelho Total)
            self.enviar_codigo_3bits(4)
            print("Via Principal: VERMELHO | Via Cruzamento: VERMELHO")
            sleep(2)
