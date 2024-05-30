import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFrame
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
import RPi.GPIO as GPIO
from time import sleep
import cv2
import pigpio
import math
from collections import deque
from BMI160_i2c import Driver  # Import the BMI160 driver

# Connect to pigpio
pi = pigpio.pi()
pi.set_servo_pulsewidth(12, 2500)

GPIO.setwarnings(False)

# GPIO setup for motors
DIR1, STEP1 = 20, 21  # Motor 1
DIR2, STEP2 = 8, 7    # Motor 2
CW, CCW = 1, 0        # Directions are now simple: CW increments, CCW decrements

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(STEP2, GPIO.OUT)

# Steps counter for both motors initialized to 0
steps_counter = {STEP1: 0, STEP2: 0}

# IMU setup
sensor = Driver(0x69)  # Initialize the IMU sensor

# Delay setup
delay = 0.0025  # You can adjust this for smoother or faster operation

# Define the FIR filter length
FILTER_LENGTH = 10
roll_filter_queue = deque(maxlen=FILTER_LENGTH)
yaw_filter_queue = deque(maxlen=FILTER_LENGTH)

def calculate_fir_average(queue):
    return sum(queue) / len(queue) if queue else 0

def step_motor(dir_pin, step_pin, direction, running):
    while running():
        GPIO.output(dir_pin, direction)
        GPIO.output(step_pin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        sleep(delay)
        if direction == CW:
            steps_counter[step_pin] += 1
        else:
            steps_counter[step_pin] -= 1
        
        if steps_counter[step_pin] == 0:
            update_steps_display()  # Update display right before breaking
            break  # Stop moving if zero is reached
        update_steps_display()

def update_steps_display():
    global mainWindow
    ax, ay, az = sensor.getMotion6()[3:6]
    roll = math.atan2(ay, az)
    roll_deg = math.degrees(roll)
    imu_angle = -roll_deg  # Invert roll to become the IMU angle
    yaw_deg = math.degrees(math.atan2(ax, az))  # Example yaw calculation
    
    # Add values to filter queues
    roll_filter_queue.append(imu_angle)
    yaw_filter_queue.append(yaw_deg)

    # Calculate filtered values
    filtered_roll = calculate_fir_average(roll_filter_queue)
    filtered_yaw = calculate_fir_average(yaw_filter_queue)

    mainWindow.stepsLabel.setText(f"Steps to zero: Motor 1: {steps_counter[STEP1]}, Motor 2: {steps_counter[STEP2]}")
    mainWindow.degreesLabel.setText(f"Angle Horizon: Motor 1: {steps_counter[STEP1] / 60:.2f}, Angle Rot: Motor 2: {steps_counter[STEP2] / 60:.2f}")
    mainWindow.imuLabel.setText(f"IMU Angle Horizon: {filtered_roll:.2f} degrees, IMU Angle Rot: {filtered_yaw:.2f} degrees")

class StepperControlApp(QApplication):
    def __init__(self, args):
        super(StepperControlApp, self).__init__(args)
        global mainWindow
        mainWindow = StepperControlWindow()
        self.main_window = mainWindow

class StepperControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.motor_threads = {}
        self.capture = cv2.VideoCapture(0)  # Open the default camera
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)  # Refresh every 100 ms for sensor data too
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.label = QLabel('Motors Stopped')
        self.video_label = QLabel()
        self.video_label.setFrameShape(QFrame.Box)
        
        self.returnToZeroButton = QPushButton('Return to Zero', self)
        self.returnToZeroButton.clicked.connect(self.reset_to_zero)
        
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(self.close)
        
        self.stepsLabel = QLabel('Steps to zero: Motor 1: 0, Motor 2: 0')
        self.degreesLabel = QLabel('Degrees: Motor 1: 0.00, Motor 2: 0.00')
        self.imuLabel = QLabel('Filtered Roll: 0.00 degrees, Filtered Yaw: 0.00 degrees')
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.returnToZeroButton)
        self.layout.addWidget(self.quitButton)
        self.layout.addWidget(self.stepsLabel)
        self.layout.addWidget(self.degreesLabel)
        self.layout.addWidget(self.imuLabel)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle('Dual Stepper Motor Control with Camera Feed and IMU')
        self.show()

    def reset_to_zero(self):
        for step_pin, count in steps_counter.items():
            if count != 0:
                dir_pin = DIR1 if step_pin == STEP1 else DIR2
                direction = CW if count < 0 else CCW  # Choose direction based on sign of the step count
                running = threading.Event()
                running.set()
                thread = threading.Thread(target=step_motor, args=(dir_pin, step_pin, direction, running.is_set))
                thread.start()
                self.motor_threads[step_pin] = (thread, running)

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame.shape
            cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 0, 0), 2)
            cv2.line(frame, (0, h // 2), (w, h // 2), (255, 0, 0), 2)

            bytes_per_line = 3 * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.video_label.setPixmap(QPixmap.fromImage(p))
        update_steps_display()  # Update sensor readings continuously

    def keyPressEvent(self, event):
        key = event.key()
        if key in [Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D] and key not in self.motor_threads:
            direction = CW if key == Qt.Key_W or key == Qt.Key_A else CCW
            running = threading.Event()
            running.set()
            thread = threading.Thread(target=self.control_motor, args=(key, running.is_set, direction))
            thread.running = running
            thread.start()
            self.motor_threads[key] = (thread, running)

    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.motor_threads:
            self.motor_threads[key][1].clear()  # Stop the thread
            self.motor_threads.pop(key)

    def control_motor(self, key, running, direction):
        if key == Qt.Key_W:
            self.label.setText('Motor 1 Moving CW')
            step_motor(DIR1, STEP1, CW, running)
        elif key == Qt.Key_S:
            self.label.setText('Motor 1 Moving CCW')
            step_motor(DIR1, STEP1, CCW, running)
        elif key == Qt.Key_A:
            self.label.setText('Motor 2 Moving CW')
            step_motor(DIR2, STEP2, CW, running)
        elif key == Qt.Key_D:
            self.label.setText('Motor 2 Moving CCW')
            step_motor(DIR2, STEP2, CCW, running)
        self.label.setText('Motor Stopped')


    def closeEvent(self, event):
        # Set servo to specific pulse width before closing
        pi.set_servo_pulsewidth(12, 500)
        self.capture.release()

if __name__ == "__main__":
    app = StepperControlApp(sys.argv)
    sys.exit(app.exec_())