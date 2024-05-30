import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import RPi.GPIO as GPIO
from time import sleep, time

# Constants for GPIO pins and motor directions
DIR1 = 20
STEP1 = 21
DIR2 = 2
STEP2 = 3
CW = 1       # Clockwise Rotation
CCW = 0      # Counterclockwise Rotation

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([DIR1, STEP1, DIR2, STEP2], GPIO.OUT)
GPIO.output([DIR1, DIR2], CW)

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def run(self):
        cap = cv2.VideoCapture(1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        frame_rate = 20  # Frame rate limit
        frame_period = 1.0 / frame_rate  # Period between frames in seconds

        while True:
            start_time = time()
            ret, cv_img = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                self.change_pixmap_signal.emit(p)
            elapsed_time = time() - start_time
            sleep_time = frame_period - elapsed_time
            if sleep_time > 0:
                sleep(sleep_time)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webcam and Stepper Motor Control")
        self.display_width = 640
        self.display_height = 480
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.image_label = QLabel(self)
        self.image_label.resize(self.display_width, self.display_height)
        layout.addWidget(self.image_label)

        btn_quit = QPushButton('Quit', self)
        btn_quit.clicked.connect(self.close)
        layout.addWidget(btn_quit)

        self.setLayout(layout)

        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)

    def closeEvent(self, event):
        self.thread.terminate()
        GPIO.cleanup()
        super(App, self).closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())
