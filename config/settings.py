"""
config/settings.py
------------------
Central configuration for the Road Rover project.
Edit values here to match your hardware setup.
"""

# ── Camera ──────────────────────────────────────────────────────────────────
CAMERA_RESOLUTION = (320, 320)      # Width x Height (pixels)
CAMERA_FORMAT      = "RGB888"

# ── YOLO Model ───────────────────────────────────────────────────────────────
# Path to the NCNN-converted YOLOv8 model directory
ROAD_MODEL_PATH   = "models/YOLOv8_Small_RDD_ncnn_model"
PERSON_MODEL_PATH = "models/yolov8n_ncnn_model"

# Detection class labels for the road-damage model
DETECTION_CLASSES = {
    0: "Crack",
    1: "Pothole",
}

# ── GPS ───────────────────────────────────────────────────────────────────────
GPS_PORT     = "/dev/ttyACM1"   # Serial port of the GPS module
GPS_BAUDRATE = 9600

# ── Arduino (Motor Controller) ────────────────────────────────────────────────
ARDUINO_PORT     = "/dev/ttyACM0"
ARDUINO_BAUDRATE = 9600

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_USER     = "hasin"
DB_PASSWORD = "12345678"
DB_NAME     = "road"

# Table that stores road-damage detections
DB_TABLE = "detected_road_conditions"

# ── Flask Servers ─────────────────────────────────────────────────────────────
MAP_SERVER_HOST   = "0.0.0.0"
MAP_SERVER_PORT   = 5000          # Map + detection dashboard

MANUAL_CTRL_HOST  = "0.0.0.0"
MANUAL_CTRL_PORT  = 5001          # Manual control + live feed

HUMAN_FOLLOW_HOST = "0.0.0.0"
HUMAN_FOLLOW_PORT = 5002          # Human-following mode

GPS_LIVE_HOST     = "0.0.0.0"
GPS_LIVE_PORT     = 5006          # Live GPS map only

# ── Map Defaults ──────────────────────────────────────────────────────────────
# Default centre when no GPS fix is available (Dhaka, Bangladesh)
DEFAULT_LAT  = 23.8103
DEFAULT_LON  = 90.4125
DEFAULT_ZOOM = 13

# ── Accelerometer (MPU-6050) ──────────────────────────────────────────────────
# I2C address – 0x68 (AD0 low) or 0x69 (AD0 high)
ACCEL_I2C_ADDRESS = 0x68
# Threshold (g) to trigger a bump/pothole alert from accelerometer
ACCEL_BUMP_THRESHOLD = 1.5
