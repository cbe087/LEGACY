import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout

def run_script(script_path):
    """ Run the given Python script by spawning a new process. """
    try:
        subprocess.Popen(['python3', script_path])
        print(f"Running: {script_path}")
    except Exception as e:
        print(f"Failed to start {script_path}: {str(e)}")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        # Set up the GUI layout
        layout = QVBoxLayout()

        # Define the paths to your scripts
        script1_path = 'latitude.py'
        script2_path = 'longetude.py'
        script3_path = 'find_celestial.py'
        startup_script_path = 'pigpiod.c'  # Path to the startup script

        # Automatically run the startup script when the application launches
        run_script(startup_script_path)

        # Create button for Program 1
        btn1 = QPushButton('Meassure Latitude (N/S)', self)
        btn1.clicked.connect(lambda: run_script(script1_path))
        layout.addWidget(btn1)

        # Create button for Program 2
        btn2 = QPushButton('Meassure Longetude (E/W)', self)
        btn2.clicked.connect(lambda: run_script(script2_path))
        layout.addWidget(btn2)

        # Create button for Program 3
        btn3 = QPushButton('Find celestial', self)
        btn3.clicked.connect(lambda: run_script(script3_path))
        layout.addWidget(btn3)

        # Set the layout on the application's window
        self.setLayout(layout)
        self.setWindowTitle('Program Selector')
        self.setGeometry(300, 300, 250, 150)  # Set window position and size

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
