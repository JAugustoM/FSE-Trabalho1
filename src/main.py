import threading
import time

import RPi.GPIO as GPIO

from gpio.mod1 import SemaforoLEDs
from gpio.mod2 import SemaforoCruzamento
from gpio.setup import setup_GPIO


def main():
    setup_GPIO()
    modelo1 = SemaforoLEDs()
    modelo2 = SemaforoCruzamento()

    thread_m1 = threading.Thread(target=modelo1.executar_ciclo, daemon=True)
    thread_m2 = threading.Thread(target=modelo2.executar_ciclo, daemon=True)

    print("Iniciando o sistema de controle de tráfego...")

    try:
        thread_m1.start()
        thread_m2.start()
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Encerrando todos os semáforos")

    finally:
        GPIO.cleanup()
        print("GPIO limpo com sucesso. Sistema desligado.")


if __name__ == "__main__":
    main()
