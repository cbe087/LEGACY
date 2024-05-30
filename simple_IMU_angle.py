from time import sleep
from BMI160_i2c import Driver
import math

print('Trying to initialize the sensor...')
sensor = Driver(0x69)  # change address if needed
print('Initialization done')

while True:
    data = sensor.getMotion6()
    ax, ay, az = data[3], data[4], data[5]

    # Calculate roll angle in degrees and invert it to get the "IMU angle"
    roll = math.atan2(ay, az)
    roll_deg = math.degrees(roll)
    imu_angle = -roll_deg  # Invert roll to become the IMU angle

    # Output the IMU angle
    print(f'IMU angle: {imu_angle:.2f} degrees')

    sleep(0.5)
