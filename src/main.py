import threading
import time

import RPi.GPIO as GPIO

from gpio.mod2 import SemaforoCruzamento
from gpio.setup import setup_GPIO


def main():
    setup_GPIO()
    cruzamento = SemaforoCruzamento()

    thread_cruzamento = threading.Thread(target=cruzamento.executar_ciclo, daemon=True)

    print("Iniciando o sistema de controle de tráfego...")

    try:
        thread_cruzamento.start()
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Encerrando todos os semáforos")

    finally:
        GPIO.cleanup()
        print("GPIO limpo com sucesso. Sistema desligado.")


if __name__ == "__main__":
    main()
