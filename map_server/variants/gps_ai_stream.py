import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import mysql.connector
import threading
import time
import serial
import folium
from flask import Flask, render_template, Response
import io
import os

# Flask app setup
app = Flask(__name__)

# Set up the camera with Picam
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# Get the absolute path of the model
model_path = "/home/hasin/yolov8n_ncnn_model"

# Load the YOLOv8 model
model = YOLO(model_path)

# Set up MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="hasin",
    password="12345678",
    database="data"
)
cursor = db.cursor()

# Lock for thread-safe database operations
db_lock = threading.Lock()

# GPS Serial port setup
gps_port = "/dev/serial0"  # Adjust based on your setup
ser = serial.Serial(gps_port, baudrate=9600, timeout=1)

# Global variables for GPS coordinates
latitude = None
longitude = None

# Function to store detection result in DB
def store_detection(name, latitude, longitude):
    try:
        query = "INSERT INTO detected_people (name, latitude, longitude) VALUES (%s, %s, %s)"
        values = (name, latitude, longitude)
        with db_lock:
            cursor.execute(query, values)
            db.commit()
            print(f"Saved detection of {name} at ({latitude}, {longitude})")
    except Exception as e:
        print(f"Error saving detection to DB: {e}")

# Function to parse GPS data
def parse_gps_data(data):
    global latitude, longitude
    try:
        parts = data.split(",")
        if parts[0] == "$GPGGA":
            if len(parts) >= 6 and parts[2] and parts[4]:
                lat_deg = float(parts[2]) // 100  # Degrees
                lat_min = float(parts[2]) % 100  # Minutes
                lon_deg = float(parts[4]) // 100  # Degrees
                lon_min = float(parts[4]) % 100  # Minutes
                lat = lat_deg + (lat_min / 60)
                lon = lon_deg + (lon_min / 60)
                if parts[3] == "S":  # South hemisphere
                    lat = -lat
                if parts[5] == "W":  # West hemisphere
                    lon = -lon
                latitude = lat
                longitude = lon
                print(f"GPS - Latitude: {lat}, Longitude: {lon}")
    except Exception as e:
        print(f"Error parsing GPS data: {e}")

# GPS data reading thread
def read_gps_data():
    try:
        while True:
            data = ser.readline()
            if data:
                decoded_data = data.decode('utf-8').strip()
                parse_gps_data(decoded_data)
            time.sleep(1)
    except Exception as e:
        print(f"Error reading GPS data: {e}")

# Start GPS thread
gps_thread = threading.Thread(target=read_gps_data)
gps_thread.daemon = True
gps_thread.start()

# Create the map using Folium
def create_map():
    gps_map = folium.Map(location=[latitude, longitude], zoom_start=13)
    folium.Marker([latitude, longitude], popup="Detected Location").add_to(gps_map)
    return gps_map

# Generate AI camera view
def generate_camera_feed():
    while True:
        frame = picam2.capture_array()
        results = model(frame)
        annotated_frame = results[0].plot()
        
        ret, jpeg = cv2.imencode('.jpg', annotated_frame)
        if ret:
            return jpeg.tobytes()

# Flask route to serve the camera feed
@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = generate_camera_feed()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Flask route to serve the map
@app.route('/')
def index():
    gps_map = create_map()
    map_html = gps_map._repr_html_()  # Convert Folium map to HTML
    return render_template('index.html', map_html=map_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)

