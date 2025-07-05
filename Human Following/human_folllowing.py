from flask import Flask, render_template, Response, request, jsonify
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import threading
import atexit
import os
 
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
 
selected_human = None
human_class_id = 0  # COCO class ID for 'person'
movement_status = "S"  # Initial movement status: Stop
 
 
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
        
        if selected_human:
            x1, y1, x2, y2 = selected_human
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Update selected human position if the person is found in the frame again
            for box in detected_humans:
                dx1, dy1, dx2, dy2 = box
                # Simple check: if the detected box overlaps with the selected box, update the position
                if (x1 < dx2 and x2 > dx1 and y1 < dy2 and y2 > dy1):  # simple overlap detection
                    selected_human = (dx1, dy1, dx2, dy2)
                    break
 
            # Movement logic (optional)
            center_x = (x1 + x2) // 2
            frame_center_x = frame.shape[1] // 2
            threshold = 50
            
            if center_x < frame_center_x - threshold:
                movement_status = "L"  # Left
            elif center_x > frame_center_x + threshold:
                movement_status = "R"  # Right
            else:
                movement_status = "F"  # Forward
        else:
            movement_status = "S"  # Stop
 
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
    """Close camera connection properly on exit."""
    if picam2 is not None:
        picam2.stop()  # Stop the Picamera2 camera
        print("? Camera stopped.")
 
atexit.register(shutdown_cleanup)
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)