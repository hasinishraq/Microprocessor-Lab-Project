"""
manual_control/server.py
------------------------
Flask server for manual rover control via web UI.

Features
--------
• MJPEG live video feed from Pi Camera
• REST endpoint to send directional commands to Arduino over serial
• Serves the static frontend (HTML / CSS / JS)

Run:
    python manual_control/server.py
    Open http://<pi-ip>:5001 in any browser on the same network.
"""

import atexit
import os
import sys
import time

import cv2
from flask import Flask, Response, jsonify, request, send_from_directory

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    MANUAL_CTRL_HOST, MANUAL_CTRL_PORT,
    CAMERA_RESOLUTION, ARDUINO_PORT, ARDUINO_BAUDRATE,
)

try:
    from picamera2 import Picamera2
    import serial as _serial
    _HW_AVAILABLE = True
except ImportError:
    _HW_AVAILABLE = False
    print("[ManualCtrl] Hardware libs not found – running in stub mode.")


# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
FRONTEND  = os.path.join(_HERE, "frontend")
CSS_DIR   = os.path.join(FRONTEND, "css")
JS_DIR    = os.path.join(FRONTEND, "script")

app     = Flask(__name__)
camera  = None
arduino = None


# ── Hardware init ─────────────────────────────────────────────────────────────

def _init_camera():
    global camera
    if not _HW_AVAILABLE or camera is not None:
        return
    try:
        camera = Picamera2()
        cfg = camera.create_preview_configuration(
            main={"size": CAMERA_RESOLUTION}
        )
        camera.configure(cfg)
        camera.start()
        print("[ManualCtrl] Camera ready.")
    except Exception as exc:
        print(f"[ManualCtrl] Camera init error: {exc}")


def _init_arduino():
    global arduino
    if not _HW_AVAILABLE or arduino is not None:
        return
    try:
        arduino = _serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
        time.sleep(2)   # wait for Arduino reset
        print(f"[ManualCtrl] Arduino connected on {ARDUINO_PORT}.")
    except Exception as exc:
        print(f"[ManualCtrl] Arduino init error: {exc}")


@app.before_request
def _ensure_hw():
    if camera is None:
        _init_camera()
    if arduino is None:
        _init_arduino()


# ── Static files ──────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND, "index.html")


@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(CSS_DIR, filename)


@app.route("/script/<path:filename>")
def serve_js(filename):
    return send_from_directory(JS_DIR, filename)


# ── Control endpoint ──────────────────────────────────────────────────────────

# Maps command + action to byte sent to Arduino
_CMD_MAP = {
    ("forward",  "start"):  b"F",
    ("backward", "start"):  b"B",
    ("left",     "start"):  b"L",
    ("right",    "start"):  b"R",
    ("stop",     "start"):  b"S",
    # Any release stops the rover
    ("forward",  "stop"):   b"S",
    ("backward", "stop"):   b"S",
    ("left",     "stop"):   b"S",
    ("right",    "stop"):   b"S",
}


@app.route("/control", methods=["POST"])
def control():
    """Accept {command, action} JSON and relay to Arduino."""
    data    = request.get_json(silent=True) or {}
    command = data.get("command", "")
    action  = data.get("action", "")
    byte    = _CMD_MAP.get((command, action))

    if byte is None:
        return jsonify({"error": "Unknown command/action"}), 400

    if arduino:
        try:
            arduino.write(byte)
            print(f"[ManualCtrl] → Arduino: {byte!r}  ({command}/{action})")
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500
    else:
        print(f"[ManualCtrl] Stub: would send {byte!r}")

    return jsonify({"ok": True, "sent": byte.decode()}), 200


# ── MJPEG video stream ────────────────────────────────────────────────────────

def _gen_frames():
    while True:
        if camera is None:
            time.sleep(0.1)
            continue
        try:
            frame     = camera.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            _, buf    = cv2.imencode(".jpg", frame_bgr)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        except Exception as exc:
            print(f"[ManualCtrl] Frame error: {exc}")
            time.sleep(0.1)


@app.route("/video_feed")
def video_feed():
    return Response(_gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ── Shutdown ──────────────────────────────────────────────────────────────────

def _cleanup():
    if camera:
        camera.stop()
        print("[ManualCtrl] Camera stopped.")
    if arduino:
        arduino.close()
        print("[ManualCtrl] Arduino disconnected.")


atexit.register(_cleanup)

if __name__ == "__main__":
    app.run(host=MANUAL_CTRL_HOST, port=MANUAL_CTRL_PORT,
            debug=False, use_reloader=False)
