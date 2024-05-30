import cv2

def main():
    # Open a handle to the default webcam
    cap = cv2.VideoCapture(0)  # '0' is typically the default ID for the primary camera

    # Set the resolution to 720p
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    try:
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()

            if not ret:
                print("Error: Failed to capture frame.")
                break

            # Display the resulting frame
            cv2.imshow('Webcam Feed', frame)

            # Press 'q' to close the window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # When everything is done, release the capture
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    # main()  # Uncomment to run the main function
    pass
