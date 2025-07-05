from flask import Flask, request, jsonify, send_from_directory, Response
import os
import cv2  # OpenCV for frame encoding
from picamera2 import Picamera2
import atexit
import time
import serial  # Make sure the serial module is imported
 
app = Flask(__name__)
 
# Define frontend paths
FRONTEND_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Frontend'))
CSS_FOLDER = os.path.join(FRONTEND_FOLDER, 'css')
SCRIPT_FOLDER = os.path.join(FRONTEND_FOLDER, 'script')
 
# Initialize serial connection to Arduino
arduino = None
camera = None
 
def initialize_serial():
    """Initialize serial connection to Arduino."""
    global arduino
    if arduino is None:
        try:
            arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=1)
            print("? Arduino connected successfully")
        except Exception as e:
            print(f"? Failed to connect to Arduino: {e}")
 
def initialize_camera():
    """Initialize Picamera2 for streaming."""
    global camera
    if camera is None:
        try:
            camera = Picamera2()
            
            config = camera.create_still_configuration(main={"size": (320, 320)})
            camera.configure(config)

            camera.start()
            print("? Camera initialized successfully.")# Use default configuration
        
        except Exception as e:
            print(f"? Failed to initialize camera: {e}")
 
@app.before_request
def before_request():
    """Ensure Arduino and Camera are initialized before handling requests."""
    if arduino is None:
        initialize_serial()
    if camera is None:
        initialize_camera()
 
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')
 
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(CSS_FOLDER, filename)
 
@app.route('/script/<path:filename>')
def serve_js(filename):
    return send_from_directory(SCRIPT_FOLDER, filename)
 
@app.route('/control', methods=['POST'])
def control():
    """Handles car movement based on button press/release."""
    data = request.get_json()
 
    if not data or 'command' not in data or 'action' not in data:
        return jsonify({'error': 'Invalid request, command or action missing'}), 400
 
    command = data['command']
    action = data['action']  # "start" (press) or "stop" (release)
 
    print(f"?? Received Command: {command}, Action: {action}")
 
    try:
        if action == "start":
            if command == 'forward':
                arduino.write(b'F')
            elif command == 'backward':
                arduino.write(b'B')
            elif command == 'left':
                arduino.write(b'L')
            elif command == 'right':
                arduino.write(b'R')
 
        elif action == "stop":
            arduino.write(b'S')  # Stop command
 
        return jsonify({'message': f'Command {command} ({action}) executed'}), 200
 
    except Exception as e:
        print(f"? Error sending command to Arduino: {e}")
        return jsonify({'error': 'Failed to send command to Arduino'}), 500
 
# MJPEG video streaming using Picamera2
def generate_video_feed():
    """Generates video frames for live streaming."""
    try:
        while True:
            frame = camera.capture_array()  # Capture a frame in RGB
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR
            _, buffer = cv2.imencode('.jpg', frame_bgr)  # Convert to JPEG
            frame_data = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
    except Exception as e:
        print(f"? Error capturing video: {e}")
 
@app.route('/video_feed')
def video_feed():
    """Video feed endpoint."""
    return Response(generate_video_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')
 
# Graceful Shutdown Cleanup
def shutdown_cleanup():
    """Close camera connection properly on exit."""
    if camera is not None:
        camera.stop()
        print("? Camera stopped.")
 
atexit.register(shutdown_cleanup)
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)