import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class WebcamGUI:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Open the video source
        self.cap = cv2.VideoCapture(0)

        # Set the resolution to 1080p
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(window, width=960, height=540)
        self.canvas.pack()

        # Button to close the application
        self.btn_quit = ttk.Button(window, text="Quit", command=self.window.destroy)
        self.btn_quit.pack(side=tk.BOTTOM)

        # Update & delay
        self.delay = 15  # milliseconds
        self.update()

        self.window.mainloop()

    def update(self):
        # Get a frame from the video source
        ret, frame = self.cap.read()

        if ret:
            # Resize the frame for display
            frame = cv2.resize(frame, (960, 540))

            # Convert the image to RGB (from BGR)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.imgtk = imgtk  # This line is necessary to prevent the image from being garbage collected

            # Draw a crosshair
            self.draw_crosshair()

        # Repeat every 'delay' milliseconds
        self.window.after(self.delay, self.update)

    def draw_crosshair(self):
        # Crosshair dimensions and position
        crosshair_color = 'red'
        x_center = 480  # Center of the canvas width
        y_center = 270  # Center of the canvas height
        crosshair_size = 20  # Length of each line segment

        # Vertical line
        self.canvas.create_line(x_center, y_center - crosshair_size, x_center, y_center + crosshair_size, fill=crosshair_color)
        # Horizontal line
        self.canvas.create_line(x_center - crosshair_size, y_center, x_center + crosshair_size, y_center, fill=crosshair_color)

def main():
    # Create a window and pass it to the WebcamGUI class
    root = tk.Tk()
    app = WebcamGUI(root, "Tkinter and OpenCV")
    
if __name__ == '__main__':
    main()
