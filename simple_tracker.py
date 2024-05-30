import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import RPi.GPIO as GPIO
from time import sleep
import serial

# Setup for serial communication with ESP32
ser = serial.Serial('/dev/serial0', 115200)

# GPIO setup for Motor 1 and Motor 2
DIR1 = 20  # Direction GPIO Pin for Motor 1
STEP1 = 21  # Step GPIO Pin for Motor 1
DIR2 = 8   # Direction GPIO Pin for Motor 2
STEP2 = 7   # Step GPIO Pin for Motor 2
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(STEP2, GPIO.OUT)

delay = 0.005  # Increased delay to smooth out motor movement

# Proportional and Integral gains for the PI controller
Kp = 0.05  # Reduced proportional gain
Ki = 0.005  # Reduced integral gain

# Integral sums
integral1 = 0
integral2 = 0

# Previous errors
prev_error1 = 0
prev_error2 = 0

# Smoothed LDR values
smooth_ldr1 = 0
smooth_ldr2 = 0
smooth_ldr3 = 0
smooth_ldr4 = 0
alpha = 0.1  # Smoothing factor

def pi_control(target, prev_error, integral):
    error = target
    integral += error
    derivative = error - prev_error
    output = Kp * error + Ki * integral
    max_step = 50  # Maximum number of steps per iteration
    output = max(-max_step, min(max_step, output))  # Limiting the output steps
    return output, error, integral

def motor_control(motor_dir_pin, motor_step_pin, direction, steps):
    GPIO.output(motor_dir_pin, direction)
    for _ in range(abs(steps)):
        GPIO.output(motor_step_pin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(motor_step_pin, GPIO.LOW)
        sleep(delay)

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        ldr_values = line.split(',')
        if len(ldr_values) == 4:
            try:
                # Apply smoothing to sensor values
                smooth_ldr1 = smooth_ldr1 * (1 - alpha) + int(ldr_values[0]) * alpha
                smooth_ldr2 = smooth_ldr2 * (1 - alpha) + int(ldr_values[1]) * alpha
                smooth_ldr3 = smooth_ldr3 * (1 - alpha) + int(ldr_values[2]) * alpha
                smooth_ldr4 = smooth_ldr4 * (1 - alpha) + int(ldr_values[3]) * alpha

                # Calculate differences
                difference1 = smooth_ldr1 - smooth_ldr2
                difference2 = smooth_ldr3 - smooth_ldr4

                # Determine motor direction based on sign of difference
                direction1 = CW if difference1 < 0 else CCW
                direction2 = CW if difference2 < 0 else CCW

                # Calculate steps using PI control
                steps1, prev_error1, integral1 = pi_control(difference1, prev_error1, integral1)
                steps2, prev_error2, integral2 = pi_control(difference2, prev_error2, integral2)

                # Execute motor control in threads to allow simultaneous operation
                threading.Thread(target=motor_control, args=(DIR1, STEP1, direction1, int(steps1))).start()
                threading.Thread(target=motor_control, args=(DIR2, STEP2, direction2, int(steps2))).start()

            except ValueError:
                print("Error: Non-integer values received. Check the data format.")
