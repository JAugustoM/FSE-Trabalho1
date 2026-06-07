import argparse
import asyncio
import os

from dotenv import load_dotenv

from distribuido.config import get_config
from distribuido.cruzamento import SemaforoCruzamento
from distribuido.hardware import HardwareController
from distribuido.network import TCPClient
from distribuido.sensores import SensorManager

parser = argparse.ArgumentParser()
parser.add_argument("cruzamento")


async def main():
    load_dotenv()

    CRUZAMENTO_ID: int

    env_value = os.getenv("CRUZAMENTO_ID")

    if env_value:
        CRUZAMENTO_ID = int(env_value)
    else:
        args = parser.parse_args()

        CRUZAMENTO_ID = 1 if not args.cruzamento else int(args.cruzamento)

    config = get_config(CRUZAMENTO_ID)
    loop = asyncio.get_running_loop()

    print(f"--- Inicializando Servidor Distribuído - Cruzamento {CRUZAMENTO_ID} ---")

    hw = HardwareController(loop, config)

    semaforo = SemaforoCruzamento(loop, hw, config.id)
    sensors = SensorManager(loop, hw, config.id)
    network = TCPClient(config, semaforo, sensors)

    await network.connect()

    await asyncio.gather(
        network.le_comandos(), network.loop_telemetria(), network.loop_alerta()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDesligando sistema. Limpando GPIO...")
        import RPi.GPIO as GPIO

        GPIO.cleanup()
