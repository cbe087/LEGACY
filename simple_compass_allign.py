import RPi.GPIO as GPIO
import smbus2
import time
import math
import numpy as np

# Compass setup
DEVICE_ADDRESS = 0x0D
REGISTER_MODE = 0x09
REGISTER_X_LSB = 0x00

# Initialize I2C (SMBus)
bus = smbus2.SMBus(1)

# Set continuous measurement mode
bus.write_byte_data(DEVICE_ADDRESS, REGISTER_MODE, 0x01)

# FIR Filter setup
num_taps = 10  # Number of filter taps
coefficients = [1.0 / num_taps] * num_taps  # Coefficients for a simple moving average
heading_buffer = np.zeros(num_taps)  # Buffer to store the last 'num_taps' heading values

def read_heading_filtered():
    global heading_buffer
    data = bus.read_i2c_block_data(DEVICE_ADDRESS, REGISTER_X_LSB, 6)
    x = (data[1] << 8) | data[0]
    y = (data[3] << 8) | data[2]
    heading = math.atan2(y, x)
    if heading < 0:
        heading += 2 * math.pi
    heading_degrees = math.degrees(heading)

    # Update buffer
    heading_buffer = np.roll(heading_buffer, -1)
    heading_buffer[-1] = heading_degrees

    # Apply FIR filter (convolution)
    filtered_heading = np.dot(coefficients, heading_buffer)
    return filtered_heading

# GPIO setup for stepper motors
DIR1, STEP1 = 8, 7
CW, CCW = 1, 0
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)

delay = 0.005  # Time between steps

# Function to rotate stepper motor
def rotate_motor(steps, direction):
    GPIO.output(DIR1, direction)
    for _ in range(steps):
        GPIO.output(STEP1, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP1, GPIO.LOW)
        time.sleep(delay)

try:
    # Rotate motor until it faces approximately North using filtered compass readings
    while True:
        filtered_heading = read_heading_filtered()
        print(f"Filtered Heading: {filtered_heading:.2f} degrees")
        if filtered_heading < 358 and filtered_heading > 2:  # Add a tolerance to stop exactly at North
            direction = CW if filtered_heading > 180 else CCW
            rotate_motor(1, direction)  # Small step adjustments
        else:
            print("Aligned with North!")
            break
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program stopped")
finally:
    GPIO.cleanup()  # Clean up GPIO to ensure it resets
    bus.close()
