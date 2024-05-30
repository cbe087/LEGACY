import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QFrame
from PyQt5.QtGui import QImage, QPixmap, QDoubleValidator
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import RPi.GPIO as GPIO
from time import sleep
import cv2
import pigpio

# Connect to pigpio
pi = pigpio.pi()
if not pi.connected:
    exit()

pi.set_servo_pulsewidth(12, 2500)

GPIO.setwarnings(False)

# GPIO setup for motors
DIR1, STEP1 = 20, 21  # Motor 1
DIR2, STEP2 = 8, 7    # Motor 2
CW, CCW = 1, 0        # Directions

GPIO.setmode(GPIO.BCM)
GPIO.setup([DIR1, STEP1, DIR2, STEP2], GPIO.OUT)

# Initial delay
delay = 0.0025

class MotorController(QObject):
    update_counter = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.abort_event = threading.Event()
        self.motors = {}
        self.motor_locks = {STEP1: threading.Lock(), STEP2: threading.Lock()}
        self.net_steps = {STEP1: 0, STEP2: 0}

    def run_motor(self, dir_pin, step_pin, direction, steps):
        with self.motor_locks[step_pin]:
            GPIO.output(dir_pin, direction)
            for _ in range(int(steps)):
                if self.abort_event.is_set():
                    break
                GPIO.output(step_pin, GPIO.HIGH)
                sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                sleep(delay)
                self.net_steps[step_pin] += 1 if direction == CW else -1
            self.update_counter.emit(step_pin, self.net_steps[step_pin])

    def add_motor(self, dir_pin, step_pin, direction, steps):
        if step_pin in self.motors and self.motors[step_pin].is_alive():
            self.stop_motor(step_pin)
        self.abort_event.clear()
        motor_thread = threading.Thread(target=self.run_motor, args=(dir_pin, step_pin, direction, steps))
        motor_thread.start()
        self.motors[step_pin] = motor_thread

    def stop_motor(self, step_pin):
        self.abort_event.set()
        if step_pin in self.motors and self.motors[step_pin].is_alive():
            self.motors[step_pin].join()

class StepperControlApp(QApplication):
    def __init__(self, args):
        super(StepperControlApp, self).__init__(args)
        self.main_window = StepperControlWindow()

class StepperControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = MotorController()
        self.initUI()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)
        
    def initUI(self):
        self.layout = QVBoxLayout()
        self.label = QLabel('Motors Stopped')
        self.video_label = QLabel()
        self.video_label.setFrameShape(QFrame.Box)
        
        self.stepsInputMotor1 = QLineEdit(self)
        self.stepsInputMotor1.setPlaceholderText("Enter revolutions for Motor 1")
        self.stepsInputMotor1.setValidator(QDoubleValidator(-10000.0, 10000.0, 3))
        
        self.stepsInputMotor2 = QLineEdit(self)
        self.stepsInputMotor2.setPlaceholderText("Enter revolutions for Motor 2")
        self.stepsInputMotor2.setValidator(QDoubleValidator(-10000.0, 10000.0, 3))
        
        self.stepsCounterMotor1 = QLabel('Motor 1 Steps: 0')
        self.stepsCounterMotor2 = QLabel('Motor 2 Steps: 0')
        
        self.moveButton = QPushButton('Move Motors', self)
        self.moveButton.clicked.connect(self.move_motors)
        
        self.abortButton = QPushButton('Abort', self)
        self.abortButton.clicked.connect(self.stop_motors)

        self.returnToZeroButton = QPushButton('Return to Zero', self)
        self.returnToZeroButton.clicked.connect(self.return_to_zero)
        
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(self.close)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.stepsInputMotor1)
        self.layout.addWidget(self.stepsInputMotor2)
        self.layout.addWidget(self.stepsCounterMotor1)
        self.layout.addWidget(self.stepsCounterMotor2)
        self.layout.addWidget(self.moveButton)
        self.layout.addWidget(self.abortButton)
        self.layout.addWidget(self.returnToZeroButton)
        self.layout.addWidget(self.quitButton)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle('Dual Stepper Motor Control with Camera Feed')
        self.show()

        # Connect signals
        self.controller.update_counter.connect(self.update_counters)

    def get_steps(self, text):
        return float(text) * 60 if text.strip() else 0

    def move_motors(self):
        steps1 = self.get_steps(self.stepsInputMotor1.text())
        steps2 = self.get_steps(self.stepsInputMotor2.text())
        direction1 = CW if steps1 >= 0 else CCW
        direction2 = CW if steps2 >= 0 else CCW
        self.controller.add_motor(DIR1, STEP1, direction1, abs(steps1))
        self.controller.add_motor(DIR2, STEP2, direction2, abs(steps2))

    def stop_motors(self):
        self.controller.stop_motor(STEP1)
        self.controller.stop_motor(STEP2)

    def return_to_zero(self):
        steps1 = self.controller.net_steps[STEP1]
        steps2 = self.controller.net_steps[STEP2]
        direction1 = CCW if steps1 > 0 else CW
        direction2 = CCW if steps2 > 0 else CW
        self.controller.add_motor(DIR1, STEP1, direction1, abs(steps1))
        self.controller.add_motor(DIR2, STEP2, direction2, abs(steps2))

    def update_counters(self, step_pin, count):
        if step_pin == STEP1:
            self.stepsCounterMotor1.setText(f'Motor 1 Steps: {count}')
        elif step_pin == STEP2:
            self.stepsCounterMotor2.setText(f'Motor 2 Steps: {count}')

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame.shape
            bytes_per_line = 3 * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.video_label.setPixmap(QPixmap.fromImage(p))

    def closeEvent(self, event):
        pi.set_servo_pulsewidth(12, 500)
        self.capture.release()
        GPIO.cleanup()  # Properly clean up GPIOs to ensure all pins are reset
        pi.stop()
        event.accept()

if __name__ == "__main__":
    app = StepperControlApp(sys.argv)
    sys.exit(app.exec_())