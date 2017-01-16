import RPi.GPIO as GPIO
from time import sleep
pin = 7
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(pin, GPIO.OUT)
#a = 0
#while (a<10):
GPIO.output(pin, GPIO.HIGH)
sleep(.5)
GPIO.output(pin, GPIO.LOW)
sleep(0.5)
#a=a+1
GPIO.cleanup()
