
import pigpio
from time import sleep

# connect to the 
pi = pigpio.pi()

pi.set_servo_pulsewidth(12,500)