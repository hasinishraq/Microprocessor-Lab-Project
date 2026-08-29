from flask import Flask, render_template, Response, request, jsonify
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import threading
import atexit
import os
import serial  # Import serial for Arduino communication

app = Flask(__name__)

# Define the model path relative to the current working directory
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yolov8n_ncnn_model')

# Initialize Camera and Model
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Initialize YOLO model with the correct path
model = YOLO(model_path)

# Initialize Arduino for movement control
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # Adjust the port for your Arduino

selected_human = None
human_class_id = 0  # COCO class ID for 'person'
movement_status = "S"  # Initial movement status: Stop

def send_arduino_command(command):
    """Send command to Arduino to control movement."""
    try:
        arduino.write(command.encode())  # Send the command as a byte string
        print(f"Sent command: {command}")
    except Exception as e:
        print(f"Error sending command to Arduino: {e}")

def generate_frames():
    global selected_human, movement_status
    while True:
        frame = picam2.capture_array()
        results = model(frame, imgsz=320)

        detected_humans = []
        for result in results[0].boxes:
            if int(result.cls) == human_class_id:
                x1, y1, x2, y2 = result.xyxy[0].tolist()
                detected_humans.append((x1, y1, x2, y2))
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)

        # If a person is selected, track their movement
        if selected_human:
            x1, y1, x2, y2 = selected_human
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            # Update selected human position if the person is found in the frame again
            person_found = False
            for box in detected_humans:
                dx1, dy1, dx2, dy2 = box
                # Check if the detected person overlaps with the selected human
                if (x1 < dx2 and x2 > dx1 and y1 < dy2 and y2 > dy1):
                    selected_human = (dx1, dy1, dx2, dy2)  # Update the selected person
                    person_found = True
                    break

            if person_found:
                # Movement logic (optional)
                center_x = (x1 + x2) // 2
                frame_center_x = frame.shape[1] // 2
                threshold = 50

                if center_x < frame_center_x - threshold:
                    movement_status = "L"  # Left
                    send_arduino_command('L')  # Send 'L' command to Arduino
                elif center_x > frame_center_x + threshold:
                    movement_status = "R"  # Right
                    send_arduino_command('R')  # Send 'R' command to Arduino
                else:
                    movement_status = "F"  # Forward
                    send_arduino_command('F')  # Send 'F' command to Arduino
            else:
                # If the person is no longer found in the frame, stop movement
                movement_status = "S"  # Stop
                send_arduino_command('S')  # Send 'S' command to Arduino
                selected_human = None  # Clear the selected human since they are no longer in the frame
        else:
            # If no person is selected or person is lost, stop movement
            movement_status = "S"  # Stop
            send_arduino_command('S')  # Send 'S' command to Arduino

        # Encode the frame for streaming
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/select_person', methods=['POST'])
def select_person():
    global selected_human
    data = request.get_json()
    x, y = data['x'], data['y']
    
    # Capture a frame for detection
    frame = picam2.capture_array()
    results = model(frame, imgsz=320)
    
    detected_humans = []
    for result in results[0].boxes:
        if int(result.cls) == human_class_id:
            x1, y1, x2, y2 = result.xyxy[0].tolist()
            detected_humans.append((x1, y1, x2, y2))
            
            # Log detected boxes and click position for debugging
            print(f"Detected box: ({x1}, {y1}), ({x2}, {y2})")
            print(f"Click position: ({x}, {y})")
            
            # Check if click is inside a detected human box
            if x1 <= x <= x2 and y1 <= y <= y2:
                selected_human = (x1, y1, x2, y2)
                return jsonify({"status": "Person selected"})
    
    return jsonify({"status": "No person found"})


@app.route('/get_movement', methods=['GET'])
def get_movement():
    return jsonify({"movement": movement_status})


def shutdown_cleanup():
    """Close camera connection and Arduino properly on exit."""
    if picam2 is not None:
        picam2.stop()  # Stop the Picamera2 camera
        print("? Camera stopped.")
    
    if arduino is not None:
        try:
            send_arduino_command('S')  # Send 'S' to Arduino to stop any movement before closing
            arduino.close()  # Close the Arduino serial connection properly
            print("? Arduino connection closed.")
        except Exception as e:
            print(f"Error during Arduino cleanup: {e}")

atexit.register(shutdown_cleanup)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)