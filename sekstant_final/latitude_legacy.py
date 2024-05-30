import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFrame
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QTimer
import RPi.GPIO as GPIO
from time import sleep
import cv2
import pigpio

# Connect to pigpio
pi = pigpio.pi()
pi.set_servo_pulsewidth(12, 2500)

GPIO.setwarnings(False)

# GPIO setup for motors
DIR1, STEP1 = 20, 21  # Motor 1
DIR2, STEP2 = 8, 7    # Motor 2
CW, CCW = 0, 1        # Directions

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(STEP2, GPIO.OUT)

# Steps counter for both motors
steps_counter = {STEP1: 0, STEP2: 0}

# Delay setup
delay = 0.0025  # You can adjust this for smoother or faster operation

def step_motor(dir_pin, step_pin, direction):
    while threading.currentThread().running:
        GPIO.output(dir_pin, direction)
        GPIO.output(step_pin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        sleep(delay)
        if direction == CW:
            steps_counter[step_pin] += 1
        else:
            steps_counter[step_pin] -= 1
        update_steps_display()

def update_steps_display():
    global mainWindow
    steps_to_zero_motor1 = abs(steps_counter[STEP1])
    steps_to_zero_motor2 = abs(steps_counter[STEP2])
    revolutions_motor1 = steps_to_zero_motor1 / 60
    revolutions_motor2 = steps_to_zero_motor2 / 60
    mainWindow.stepsLabel.setText(f"Steps to zero: Motor 1: {steps_to_zero_motor1}, Motor 2: {steps_to_zero_motor2}")
    mainWindow.revolutionsLabel.setText(f"Revolutions to zero: Motor 1: {revolutions_motor1:.2f}, Motor 2: {revolutions_motor2:.2f}")

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
        self.timer.start(20)  # Refresh every 20 ms
        
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
        self.revolutionsLabel = QLabel('Degrees: Motor 1: 0.00, Motor 2: 0.00')
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.returnToZeroButton)
        self.layout.addWidget(self.quitButton)
        self.layout.addWidget(self.stepsLabel)
        self.layout.addWidget(self.revolutionsLabel)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle('Dual Stepper Motor Control with Camera Feed')
        self.show()

    def reset_to_zero(self):
        for step_pin, count in steps_counter.items():
            dir_pin = DIR1 if step_pin == STEP1 else DIR2
            direction = CW if count > 0 else CCW
            threading.Thread(target=step_motor, args=(dir_pin, step_pin, direction)).start()
            steps_counter[step_pin] = 0
        update_steps_display()
        self.label.setText('Motors Reset to Zero Position')

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

    def keyPressEvent(self, event):
        key = event.key()
        if key in [Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D] and key not in self.motor_threads:
            thread = threading.Thread(target=self.control_motor, args=(key,))
            thread.running = True
            thread.start()
            self.motor_threads[key] = thread

    def keyReleaseEvent(self, event):
        key = event.key()
        if key in self.motor_threads:
            self.motor_threads[key].running = False
            self.motor_threads.pop(key)

    def control_motor(self, key):
        if key == Qt.Key_S:
            self.label.setText('Motor 1 Moving Down')
            step_motor(DIR1, STEP1, CW)
        elif key == Qt.Key_W:
            self.label.setText('Motor 1 Moving Up')
            step_motor(DIR1, STEP1, CCW)
        elif key == Qt.Key_A:
            self.label.setText('Motor 2 Moving Clockwise')
            step_motor(DIR2, STEP2, CW)
        elif key == Qt.Key_D:
            self.label.setText('Motor 2 Moving Counterclockwise')
            step_motor(DIR2, STEP2, CCW)
        self.label.setText('Motor Stopped')

    def closeEvent(self, event):
        # Set servo to specific pulse width before closing
        pi.set_servo_pulsewidth(12, 500)
        self.capture.release()

if __name__ == "__main__":
    app = StepperControlApp(sys.argv)
    sys.exit(app.exec_())