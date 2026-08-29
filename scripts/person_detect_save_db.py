import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import mysql.connector
import threading
import time
import serial
 
# Set up the camera with Picam
picam2 = Picamera2()
picam2.preview_configuration.main.size = (320, 320)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()
 
# Load the YOLOv8 model
model = YOLO("yolov8n_ncnn_model")
 
# Set up MySQL database connection
db = mysql.connector.connect(
    host="localhost",        # Your database host (e.g., localhost)
    user="hasin",        # Your database username
    password="12345678",  # Your database password
    database="data"       # Your database name
)
cursor = db.cursor()
 
# Lock for thread-safe database operations
db_lock = threading.Lock()
 
# GPS Serial port setup (Assuming GPS module connected to /dev/serial0, adjust based on your setup)
gps_port = "/dev/serial0"  # Replace with the correct port for your GPS
ser = serial.Serial(gps_port, baudrate=9600, timeout=1)
 
# Global variables to store GPS coordinates
latitude = None
longitude = None
 
def store_detection(name, latitude, longitude):
    """Store detection result into the MySQL database."""
    try:
        query = "INSERT INTO detected_people (name, latitude, longitude) VALUES (%s, %s, %s)"
        values = (name, latitude, longitude)
        
        with db_lock:
            cursor.execute(query, values)
            db.commit()
            print(f"Saved detection of {name} at ({latitude}, {longitude})")
    except Exception as e:
        print(f"Error saving detection to DB: {e}")
 
def parse_gps_data(data):
    """Parse the NMEA sentence to extract latitude and longitude."""
    global latitude, longitude
    try:
        parts = data.split(",")
        
        # Handle $GPGGA sentence: Global Positioning System Fix Data
        if parts[0] == "$GPGGA":
            # Ensure there are enough parts and check if latitude and longitude are available
            if len(parts) >= 6 and parts[2] and parts[4]:
                lat_deg = float(parts[2]) // 100  # Degrees (before the dot)
                lat_min = float(parts[2]) % 100  # Minutes (after the dot)
                lon_deg = float(parts[4]) // 100  # Degrees (before the dot)
                lon_min = float(parts[4]) % 100  # Minutes (after the dot)
                
                # Convert minutes to decimal degrees
                lat = lat_deg + (lat_min / 60)
                lon = lon_deg + (lon_min / 60)
                
                # Apply direction
                if parts[3] == "S":  # South hemisphere
                    lat = -lat
                if parts[5] == "W":  # West hemisphere
                    lon = -lon
 
                latitude = lat
                longitude = lon
                print(f"GPS - Latitude: {lat}, Longitude: {lon}")
            else:
                print("Invalid data in $GPGGA sentence (missing latitude or longitude).")
                
    except Exception as e:
        print(f"Error parsing GPS data: {e}")
 
def read_gps_data():
    """Read and process GPS data indefinitely."""
    try:
        while True:
            data = ser.readline()
            if data:
                decoded_data = data.decode('utf-8').strip()  # Decode the data
                parse_gps_data(decoded_data)  # Parse the NMEA sentence for GPS info
            time.sleep(1)  # Delay to avoid overwhelming the output
    except Exception as e:
        print(f"Error reading GPS data: {e}")
 
# Start the GPS reading in a separate thread
gps_thread = threading.Thread(target=read_gps_data)
gps_thread.daemon = True  # Allows the thread to exit when the main program ends
gps_thread.start()
 
while True:
    # Capture a frame from the camera
    frame = picam2.capture_array()
    
    # Run YOLO model on the captured frame
    results = model(frame)
    
    # Annotate the frame with detection results
    annotated_frame = results[0].plot()
 
    # Get inference time and FPS
    inference_time = results[0].speed['inference']
    fps = 1000 / inference_time  # Convert to milliseconds
    text = f'FPS: {fps:.1f}'
 
    # Define font and position for FPS display
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = annotated_frame.shape[1] - text_size[0] - 10  # 10 pixels from the right
    text_y = text_size[1] + 10  # 10 pixels from the top
 
    # Draw FPS text on the frame
    cv2.putText(annotated_frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
 
    # Loop through detections to check for the "person" class
    for obj in results[0].boxes:
        # Get the label (class) of the detected object
        label = int(obj.cls[0])  # Convert to int
        
        # Check if the detected object is a "person"
        if label == 0:  # Class 0 corresponds to "person" in COCO dataset for YOLO
            # Store "Person" as the name
            name = "Person"
            if latitude is not None and longitude is not None:
                store_detection(name, latitude, longitude)  # Store the detection in the database
 
    # Display the annotated frame
    cv2.imshow("Camera", annotated_frame)
 
    # Exit the program if 'q' is pressed
    if cv2.waitKey(1) == ord("q"):
        break
 
# Clean up and close all windows
cv2.destroyAllWindows()
picam2.stop()
cursor.close()
db.close()
