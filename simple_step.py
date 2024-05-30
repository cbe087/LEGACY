import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import RPi.GPIO as GPIO
from time import sleep

GPIO.setwarnings(False)

# GPIO setup for Motor 1
DIR1 = 20    # Direction GPIO Pin for Motor 1
STEP1 = 21   # Step GPIO Pin for Motor 1
# GPIO setup for Motor 2
DIR2 = 8     # Direction GPIO Pin for Motor 2
STEP2 = 7    # Step GPIO Pin for Motor 2

CW = 1       # Clockwise Rotation
CCW = 0      # Counterclockwise Rotation

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(STEP1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(STEP2, GPIO.OUT)

delay = 0.0025

def step_motor(dir_pin, step_pin, direction):
    while threading.currentThread().running:
        GPIO.output(dir_pin, direction)
        GPIO.output(step_pin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        sleep(delay)

class StepperControlApp(QApplication):
    def __init__(self, args):
        super(StepperControlApp, self).__init__(args)
        self.main_window = StepperControlWindow()

class StepperControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.motor_threads = {}

    def initUI(self):
        self.layout = QVBoxLayout()
        self.label = QLabel('Motors Stopped')
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Dual Stepper Motor Control')
        self.show()

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
        if key == Qt.Key_W:
            self.label.setText('Motor 1 Moving Clockwise')
            step_motor(DIR1, STEP1, CW)
        elif key == Qt.Key_S:
            self.label.setText('Motor 1 Moving Counterclockwise')
            step_motor(DIR1, STEP1, CCW)
        elif key == Qt.Key_A:
            self.label.setText('Motor 2 Moving Clockwise')
            step_motor(DIR2, STEP2, CW)
        elif key == Qt.Key_D:
            self.label.setText('Motor 2 Moving Counterclockwise')
            step_motor(DIR2, STEP2, CCW)
        self.label.setText('Motor Stopped')

if __name__ == "__main__":
    app = StepperControlApp(sys.argv)
    sys.exit(app.exec_())
W