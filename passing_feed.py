from flask import Flask, Response
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO

app = Flask(__name__)

# Set up the camera with Picamera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Load YOLO model
model = YOLO("yolov8n_ncnn_model")

def gen_frames():
    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()

        # Run YOLO model on the captured frame and store the results
        results = model(frame)

        # Annotate the frame with the detection data
        annotated_frame = results[0].plot()

        # Convert frame to JPEG format to stream it over HTTP
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
        
        # Yield the frame in the correct format for MJPEG streaming
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return "Flask server is running. Go to /video_feed for the video stream."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
