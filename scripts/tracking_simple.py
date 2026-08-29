import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import time

# Set up the camera with Picamera2
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Load YOLOv8 model
model = YOLO("yolov8n_ncnn_model")

# Define human class ID (COCO index for 'person' is 0)
human_class_id = 0

while True:
    frame = picam2.capture_array()
    results = model(frame, imgsz=320)

    humans = []
    for result in results[0].boxes:
        if int(result.cls) == human_class_id:
            x1, y1, x2, y2 = result.xyxy[0].tolist()
            confidence = result.conf[0].item()
            humans.append((x1, y1, x2, y2, confidence))

    if humans:
        # Select the closest human based on bounding box size
        humans.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
        target_human = humans[0]

        x1, y1, x2, y2, _ = target_human
        center_x = (x1 + x2) // 2

        # Draw the selected human bounding box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, "Tracking", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Determine movement based on position
        frame_center_x = frame.shape[1] // 2
        threshold = 50

        if center_x < frame_center_x - threshold:
            movement = "L"  # Left
        elif center_x > frame_center_x + threshold:
            movement = "R"  # Right
        else:
            movement = "F"  # Forward
    else:
        movement = "S"  # Stop if no humans detected

    # Print the movement direction
    print(f"Movement: {movement}")

    # Show the frame
    cv2.imshow("Camera", frame)

    # Exit the program if 'q' is pressed
    if cv2.waitKey(1) == ord("q"):
        break

# Clean up
cv2.destroyAllWindows()
