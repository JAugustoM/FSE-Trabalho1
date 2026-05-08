import RPi.GPIO as GPIO

# GPIO Modelo 1
LED0: int = 17
LED1: int = 18
LED2: int = 23
LEDS = [LED0, LED1, LED2]

BOTP_M1: int = 1
BOTC_M1: int = 12
BOTSM1 = [BOTP_M1, BOTC_M1]

# GPIO Modelo 2
SEM0: int = 24
SEM1: int = 8
SEM2: int = 7
SEMS = [SEM0, SEM1, SEM2]

BOTP_M2: int = 25
BOTC_M2: int = 22
BOTSM2 = [BOTP_M2, BOTC_M2]


def setup_mod1():
    GPIO.setup(LEDS, GPIO.OUT)
    GPIO.output(LEDS, GPIO.LOW)

    GPIO.setup(BOTSM1, GPIO.IN, GPIO.PUD_DOWN)


def setup_mod2():
    GPIO.setup(SEMS, GPIO.OUT)
    GPIO.output(SEMS, GPIO.LOW)

    GPIO.setup(BOTSM2, GPIO.IN, GPIO.PUD_DOWN)


def setup_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    setup_mod1()
    setup_mod2()
