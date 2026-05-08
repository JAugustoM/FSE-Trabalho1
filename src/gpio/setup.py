import RPi.GPIO as gpio

# GPIO Modelo 1
LED0: int = 17
LED1: int = 18
LED2: int = 23

BOTP_M1: int = 1
BOTC_M1: int = 12

# GPIO Modelo 2
SEM0: int = 24
SEM1: int = 8
SEM2: int = 7

BOTP_M2: int = 25
BOTC_M2: int = 22


def setup_mod1():
    gpio.output(LED0, gpio.LOW)
    gpio.output(LED1, gpio.LOW)
    gpio.output(LED2, gpio.LOW)

    gpio.input(BOTP_M1)
    gpio.input(BOTC_M1)


def setup_mod2():
    gpio.output(SEM0, gpio.LOW)
    gpio.output(SEM1, gpio.LOW)
    gpio.output(SEM2, gpio.LOW)

    gpio.input(BOTP_M2)
    gpio.input(BOTC_M2)


def setup_gpio():
    gpio.setmode(gpio.BCM)
    setup_mod1()
    setup_mod2()
