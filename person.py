from flask import Flask, render_template, Response, request, jsonify
import cv2
import serial
from picamera2 import Picamera2
from ultralytics import YOLO
import threading

app = Flask(__name__)

# Initialize Camera and Model
picam2 = Picamera2()

# Configure camera
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

model = YOLO("yolov8n_ncnn_model")

selected_human = None
human_class_id = 0  # COCO class ID for 'person'


def generate_frames():
    global selected_human
    while True:
        # Capture frame
        frame = picam2.capture_array()
        results = model(frame, imgsz=320)
        
        detected_humans = []
        for result in results[0].boxes:
            if int(result.cls) == human_class_id:
                x1, y1, x2, y2 = result.xyxy[0].tolist()
                detected_humans.append((x1, y1, x2, y2))
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        
        if selected_human:
            x1, y1, x2, y2 = selected_human
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Movement logic
            center_x = (x1 + x2) // 2
            frame_center_x = frame.shape[1] // 2
            threshold = 50
            
            if center_x < frame_center_x - threshold:
                movement = "L"  # Left
            elif center_x > frame_center_x + threshold:
                movement = "R"  # Right
            else:
                movement = "F"  # Forward
            
            print(f"Movement Command: {movement}")  # Print command instead of sending to Arduino
        else:
            print("Movement Command: S")  # Print 'Stop' command

        # Convert frame to jpeg
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
    
    # Check if click is inside a detected human box
    for result in model(picam2.capture_array(), imgsz=320)[0].boxes:
        if int(result.cls) == human_class_id:
            x1, y1, x2, y2 = result.xyxy[0].tolist()
            if x1 <= x <= x2 and y1 <= y <= y2:
                selected_human = (x1, y1, x2, y2)
                return jsonify({"status": "Person selected"})
    
    return jsonify({"status": "No person found"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
