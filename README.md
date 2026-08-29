<div align="center">

# 🚗 Road Rover

### AI-Powered Road Damage Detection & Mapping System

[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4B%208GB-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-NCNN-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://ultralytics.com/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> An autonomous rover that detects **potholes** and **road cracks** in real-time using YOLOv8 computer vision, pins every event on an interactive GPS map, and is remotely controllable from any browser on the same network.

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🏗️ Project Structure](#️-project-structure)
- [🔧 Hardware](#-hardware)
  - [Wiring Diagram](#wiring-diagram)
- [⚙️ Software Setup](#️-software-setup)
  - [1. OS & System Packages](#1-os--system-packages)
  - [2. Clone the Repository](#2-clone-the-repository)
  - [3. Python Environment](#3-python-environment)
  - [4. Database Setup](#4-database-setup)
  - [5. Configure Settings](#5-configure-settings)
  - [6. Download YOLO Models](#6-download-yolo-models)
- [🚀 Running the Rover](#-running-the-rover)
  - [Detection Mode](#detection-mode)
  - [Map Dashboard](#map-dashboard)
  - [Manual Control](#manual-control)
  - [Human-Following Mode](#human-following-mode)
- [🗂️ Module Reference](#️-module-reference)
- [🗄️ Database Schema](#️-database-schema)
- [🛠️ Arduino Firmware](#️-arduino-firmware)
- [📡 API Reference](#-api-reference)
- [🤝 Contributing](#-contributing)
- [👥 Team Members](#-team-members)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **AI Detection** | Real-time pothole & crack detection with YOLOv8 NCNN (optimised for Raspberry Pi) |
| 🗺️ **GPS Mapping** | Every detection is tagged with latitude/longitude and pinned on a Folium/Leaflet map |
| 📳 **Accelerometer Fusion** | MPU-6050 cross-validates vision detections with physical bump events |
| 🎮 **Manual Control** | Browser-based D-pad + WASD/Arrow-key rover control with live MJPEG feed |
| 🚶 **Human Following** | Click-to-track a person; rover steers autonomously to keep the target centred |
| 📊 **Live Dashboard** | Dark-mode web dashboard with detection statistics, auto-refresh map & REST API |
| 💾 **Persistent Storage** | All detections saved to MySQL with timestamps, confidence scores and source |
| 🔌 **Modular Codebase** | Clean Python packages – swap any sensor or model without touching unrelated code |

---

## 🏗️ Project Structure

```
Microprocessor-Lab-Project/
│
├── config/                     # 🔧 Centralised configuration
│   └── settings.py             #    Ports, credentials, thresholds – edit here
│
├── gps/                        # 📡 GPS module interface
│   ├── __init__.py
│   └── parser.py               #    Thread-safe NMEA parser (GPGGA + GPRMC)
│
├── sensors/                    # 📳 Physical sensors
│   ├── __init__.py
│   └── accelerometer.py        #    MPU-6050 I²C reader & bump detector
│
├── database/                   # 🗄️ Database layer
│   ├── __init__.py
│   ├── db_helper.py            #    Thread-safe MySQL helper (insert / fetch)
│   └── schema.sql              #    Table definitions – run once to initialise
│
├── detection/                  # 🔍 Core detection pipeline
│   ├── __init__.py
│   └── road_detector.py        #    Camera + YOLO + GPS + Accel + DB integration
│
├── map_server/                 # 🗺️ Web map dashboard
│   ├── __init__.py
│   ├── app.py                  #    Flask app: /, /api/data, /api/stats
│   └── templates/
│       └── index.html          #    Dark-mode dashboard with Folium map
│
├── manual_control/             # 🎮 Remote rover control
│   ├── __init__.py
│   ├── server.py               #    Flask server + Arduino serial relay
│   └── frontend/
│       ├── index.html          #    D-pad UI (touch + keyboard)
│       ├── css/style.css
│       └── script/script.js
│
├── human_following/            # 🚶 Autonomous human-following mode
│   ├── __init__.py
│   ├── follower.py             #    YOLOv8 person tracking + Arduino steering
│   └── templates/
│       └── index.html          #    Click-to-select tracking UI
│
├── models/                     # 🤖 YOLO model files (not committed – download separately)
│   ├── YOLOv8_Small_RDD_ncnn_model/
│   └── yolov8n_ncnn_model/
│
├── requirements.txt            # 📦 Python dependencies
├── .gitignore
└── README.md
```

---

## 🔧 Hardware

### Bill of Materials

| Component | Model / Spec | Purpose |
|---|---|---|
| **Main Computer** | Raspberry Pi 4B 8 GB | Processing, networking, running all Python modules |
| **Camera** | Raspberry Pi Camera Module 3 (or v2) | Real-time video stream for YOLO inference |
| **GPS Module** | NEO-6M / NEO-8M (UART, NMEA 0183) | Geolocation tagging of detections |
| **Accelerometer** | MPU-6050 (I²C, 6-axis) | Physical bump / pothole cross-validation |
| **Motor Controller** | Arduino Uno + L298N H-Bridge | DC motor control for 4WD chassis |
| **Chassis** | 4WD Robot Car Platform | Rover body |
| **Power** | 3S LiPo or USB power bank | Raspberry Pi + Arduino + motors |

---

### Wiring Diagram

```
Raspberry Pi 4
──────────────────────────────────────────────────────────
 Pin  3 (GPIO 2 / SDA)  ──────────────────── MPU-6050 SDA
 Pin  5 (GPIO 3 / SCL)  ──────────────────── MPU-6050 SCL
 Pin  1 (3.3 V)         ──────────────────── MPU-6050 VCC
 Pin  6 (GND)           ──────────────────── MPU-6050 GND
                                             MPU-6050 AD0 ── GND (addr 0x68)

 USB-A Port             ──────────────────── GPS Module (USB/UART adapter)
                                             Default: /dev/ttyACM1

 USB-A Port             ──────────────────── Arduino Uno
                                             Default: /dev/ttyACM0

 CSI Connector          ──────────────────── Pi Camera Module
──────────────────────────────────────────────────────────

Arduino Uno  ←→  L298N H-Bridge  ←→  4× DC Motors
  Serial 'F' → Forward | 'B' → Backward
  'L' → Left  | 'R' → Right  | 'S' → Stop
```

> **Tip:** Run `ls /dev/tty*` before and after plugging in each USB device to identify the correct port. Update `config/settings.py` accordingly.

---

## ⚙️ Software Setup

### 1. OS & System Packages

Flash **Raspberry Pi OS (64-bit, Bookworm)** and then:

```bash
sudo apt update && sudo apt upgrade -y

# Camera
sudo apt install -y libcamera-apps python3-picamera2

# OpenCV native deps
sudo apt install -y python3-opencv

# MySQL server
sudo apt install -y mariadb-server

# I²C tools (for accelerometer testing)
sudo apt install -y i2c-tools python3-smbus2
sudo raspi-config   # → Interface Options → I2C → Enable
```

### 2. Clone the Repository

```bash
git clone https://github.com/hasinishraq/Microprocessor-Lab-Project.git
cd Microprocessor-Lab-Project
```

### 3. Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Setup

```bash
sudo mysql -u root
```

```sql
CREATE USER 'hasin'@'localhost' IDENTIFIED BY '12345678';
GRANT ALL PRIVILEGES ON road.* TO 'hasin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
mysql -u hasin -p < database/schema.sql
```

### 5. Configure Settings

Open [`config/settings.py`](config/settings.py) and verify every value matches your hardware:

```python
GPS_PORT      = "/dev/ttyACM1"   # ← check with: ls /dev/tty*
ARDUINO_PORT  = "/dev/ttyACM0"
DB_PASSWORD   = "12345678"       # ← change in production!
```

### 6. Download YOLO Models

> Model weights are **not committed** to the repository (large binary files). Place them in the `models/` directory.

```bash
mkdir -p models
```

**Road Damage Detection model** (YOLOv8 NCNN):

Download the pre-trained Road Damage Detection model converted to NCNN format and extract into `models/YOLOv8_Small_RDD_ncnn_model/`.

**Person Detection model** (standard YOLOv8n NCNN):

```bash
# Using Ultralytics export from a machine with more RAM:
yolo export model=yolov8n.pt format=ncnn
# Then copy yolov8n_ncnn_model/ to models/ on the Pi
```

---

## 🚀 Running the Rover

> All commands assume you are in the project root with the virtual environment activated.

### Detection Mode

Starts the main detection pipeline: camera → YOLO → GPS → database.

```bash
# With display (local screen)
python detection/road_detector.py

# Headless (SSH session, no monitor)
python detection/road_detector.py --headless

# Increase save interval to reduce DB writes
python detection/road_detector.py --headless --interval 5.0
```

Press **`q`** (or Ctrl-C in headless mode) to stop.

---

### Map Dashboard

Shows all stored detections on an interactive map with statistics.

```bash
python map_server/app.py
```

Open **`http://<pi-ip>:5000`** in any browser on the same Wi-Fi network.

| Endpoint | Description |
|---|---|
| `GET /` | Full map dashboard |
| `GET /api/data` | All detections as JSON |
| `GET /api/stats` | Per-type counts as JSON |

---

### Manual Control

Control the rover remotely with a D-pad or WASD/arrow keys.

```bash
python manual_control/server.py
```

Open **`http://<pi-ip>:5001`**

- **Mouse/touch:** hold D-pad buttons to move, release to stop
- **Keyboard:** `W A S D` or `↑ ↓ ← →` · `Space` to stop

---

### Human-Following Mode

```bash
python human_following/follower.py
```

Open **`http://<pi-ip>:5002`**

1. The live feed is displayed in the browser.
2. **Click** on any person in the frame to start tracking.
3. The rover will steer to keep the selected person centred.
4. Click **Stop Tracking** to disengage.

---

## 🗂️ Module Reference

| Module | Entry Point | Port |
|---|---|---|
| Road Detection | `detection/road_detector.py` | — |
| Map Dashboard | `map_server/app.py` | 5000 |
| Manual Control | `manual_control/server.py` | 5001 |
| Human Following | `human_following/follower.py` | 5002 |
| GPS Reader only | `gps/parser.py` | — |
| Accelerometer only | `sensors/accelerometer.py` | — |

---

## 🗄️ Database Schema

```sql
CREATE TABLE detected_road_conditions (
    id           INT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(50)    NOT NULL,        -- 'Pothole' | 'Crack' | 'BumpEvent'
    latitude     DECIMAL(10,7)  NOT NULL,
    longitude    DECIMAL(10,7)  NOT NULL,
    confidence   FLOAT          DEFAULT NULL,    -- YOLO confidence 0–1
    source       VARCHAR(20)    DEFAULT 'vision',-- 'vision' | 'accelerometer' | 'combined'
    detected_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🛠️ Arduino Firmware

The Arduino acts as a serial-to-motor bridge. Upload the following sketch:

```cpp
// arduino/rover_control/rover_control.ino
// Motor pins – adjust for your L298N wiring
#define ENA 5   // Left  PWM
#define IN1 6
#define IN2 7
#define ENB 10  // Right PWM
#define IN3 8
#define IN4 9

#define SPEED 180

void setup() {
  Serial.begin(9600);
  pinMode(ENA,OUTPUT); pinMode(IN1,OUTPUT); pinMode(IN2,OUTPUT);
  pinMode(ENB,OUTPUT); pinMode(IN3,OUTPUT); pinMode(IN4,OUTPUT);
  stop();
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if      (cmd == 'F') forward();
    else if (cmd == 'B') backward();
    else if (cmd == 'L') turnLeft();
    else if (cmd == 'R') turnRight();
    else if (cmd == 'S') stop();
  }
}

void forward()  { analogWrite(ENA,SPEED); analogWrite(ENB,SPEED); digitalWrite(IN1,HIGH); digitalWrite(IN2,LOW);  digitalWrite(IN3,HIGH); digitalWrite(IN4,LOW);  }
void backward() { analogWrite(ENA,SPEED); analogWrite(ENB,SPEED); digitalWrite(IN1,LOW);  digitalWrite(IN2,HIGH); digitalWrite(IN3,LOW);  digitalWrite(IN4,HIGH); }
void turnLeft() { analogWrite(ENA,SPEED); analogWrite(ENB,SPEED); digitalWrite(IN1,LOW);  digitalWrite(IN2,HIGH); digitalWrite(IN3,HIGH); digitalWrite(IN4,LOW);  }
void turnRight(){ analogWrite(ENA,SPEED); analogWrite(ENB,SPEED); digitalWrite(IN1,HIGH); digitalWrite(IN2,LOW);  digitalWrite(IN3,LOW);  digitalWrite(IN4,HIGH); }
void stop()     { analogWrite(ENA,0);     analogWrite(ENB,0); }
```

Place the sketch in `arduino/rover_control/rover_control.ino` and upload it using the Arduino IDE or `arduino-cli`.

---

## 📡 API Reference

### `POST /control` — Manual Control Server

```json
{ "command": "forward", "action": "start" }
```

| `command` | `action` | Byte sent to Arduino |
|---|---|---|
| `forward` | `start` | `F` |
| `backward` | `start` | `B` |
| `left` | `start` | `L` |
| `right` | `start` | `R` |
| `stop` | `start` | `S` |
| any | `stop` | `S` |

### `POST /select_person` — Human Following

```json
{ "x": 160.0, "y": 200.0 }
```

Returns `{ "status": "selected" | "not_found" | "hw_unavailable" }`.

### `POST /deselect` — Human Following

Stops tracking and sends stop command to Arduino.

### `GET /api/data` — Map Server

Returns a JSON array of all detections.

### `GET /api/stats` — Map Server

Returns `{ "Pothole": 12, "Crack": 5, "BumpEvent": 3 }`.

---

## 🤝 Contributing

Pull requests are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "feat: add my feature"`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

---

## 👥 Team Members

| Name | Role |
|------|------|
| **Md. Hasin Ishraq** | Team Leader |
| Umme Sanjida Zaman | Member |
| Urmi Urma Snigdha | Member |
| Sayeda Nahiyan Ferdous | Member |
| Sayed Mahir Daiyan | Member |

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.
