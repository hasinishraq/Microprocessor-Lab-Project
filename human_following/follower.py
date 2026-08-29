"""
human_following/follower.py
---------------------------
Human-following mode using YOLOv8 + Pi Camera + Arduino motor control.

How it works
------------
1. Pi Camera captures a 320×320 frame.
2. YOLOv8 detects all people in the frame.
3. The user taps the live feed in the browser to select a target person.
4. The rover steers left/right/forward to keep the target centred.

Run:
    python human_following/follower.py
    Open http://<pi-ip>:5002
"""

import os
import sys
import time
import atexit
import threading

import cv2
from flask import Flask, Response, jsonify, render_template, request

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    HUMAN_FOLLOW_HOST, HUMAN_FOLLOW_PORT,
    CAMERA_RESOLUTION, CAMERA_FORMAT,
    PERSON_MODEL_PATH,
    ARDUINO_PORT, ARDUINO_BAUDRATE,
)

try:
    from picamera2    import Picamera2
    from ultralytics  import YOLO
    import serial as _serial
    _HW_AVAILABLE = True
except ImportError:
    _HW_AVAILABLE = False
    print("[Follower] Hardware libs unavailable – stub mode.")


app = Flask(__name__)

# ── Shared state ──────────────────────────────────────────────────────────────
_camera         = None
_model          = None
_arduino        = None
_selected_box   = None          # (x1, y1, x2, y2) of currently tracked person
_movement       = "S"           # current movement command
_frame_lock     = threading.Lock()
_latest_frame   = None          # most recent annotated frame bytes

_HUMAN_CLASS    = 0             # COCO class 0 = person
_CENTRE_TOL     = 50            # pixel tolerance around centre


# ── Hardware init ─────────────────────────────────────────────────────────────

def _init_hw():
    global _camera, _model, _arduino
    if not _HW_AVAILABLE:
        return

    _camera = Picamera2()
    cfg = _camera.create_preview_configuration(
        main={"size": CAMERA_RESOLUTION, "format": CAMERA_FORMAT}
    )
    _camera.configure(cfg)
    _camera.start()

    _model = YOLO(PERSON_MODEL_PATH)

    try:
        _arduino = _serial.Serial(ARDUINO_PORT, ARDUINO_BAUDRATE, timeout=1)
        time.sleep(2)
    except Exception as exc:
        print(f"[Follower] Arduino unavailable: {exc}")


def _send_cmd(cmd: str):
    global _movement
    _movement = cmd
    if _arduino:
        _arduino.write(cmd.encode())


# ── Detection loop (background thread) ───────────────────────────────────────

def _detect_loop():
    global _selected_box, _latest_frame

    while True:
        if _camera is None or _model is None:
            time.sleep(0.1)
            continue

        frame   = _camera.capture_array()
        results = _model(frame, imgsz=320, verbose=False)
        humans  = []

        for box in results[0].boxes:
            if int(box.cls) == _HUMAN_CLASS:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                humans.append((x1, y1, x2, y2))
                cv2.rectangle(frame,
                               (int(x1), int(y1)), (int(x2), int(y2)),
                               (80, 120, 255), 2)

        if _selected_box:
            sx1, sy1, sx2, sy2 = _selected_box

            # Re-lock onto the person in the next frame (IoU overlap check)
            for bx1, by1, bx2, by2 in humans:
                if bx1 < sx2 and bx2 > sx1 and by1 < sy2 and by2 > sy1:
                    _selected_box = (bx1, by1, bx2, by2)
                    sx1, sy1, sx2, sy2 = _selected_box
                    break

            cv2.rectangle(frame,
                           (int(sx1), int(sy1)), (int(sx2), int(sy2)),
                           (0, 255, 100), 3)

            centre_x     = (sx1 + sx2) / 2
            frame_centre = frame.shape[1] / 2

            if centre_x < frame_centre - _CENTRE_TOL:
                _send_cmd("L")
            elif centre_x > frame_centre + _CENTRE_TOL:
                _send_cmd("R")
            else:
                _send_cmd("F")
        else:
            _send_cmd("S")

        _, buf = cv2.imencode(".jpg", frame)
        with _frame_lock:
            _latest_frame = buf.tobytes()


# ── MJPEG generator ───────────────────────────────────────────────────────────

def _gen_stream():
    while True:
        with _frame_lock:
            frame = _latest_frame
        if frame:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.03)


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(_gen_stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/select_person", methods=["POST"])
def select_person():
    """User tapped the video feed – try to lock onto a person at (x, y)."""
    global _selected_box
    data = request.get_json(silent=True) or {}
    x, y = float(data.get("x", 0)), float(data.get("y", 0))

    if _camera is None or _model is None:
        return jsonify({"status": "hw_unavailable"})

    frame   = _camera.capture_array()
    results = _model(frame, imgsz=320, verbose=False)

    for box in results[0].boxes:
        if int(box.cls) != _HUMAN_CLASS:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        if x1 <= x <= x2 and y1 <= y <= y2:
            _selected_box = (x1, y1, x2, y2)
            return jsonify({"status": "selected"})

    _selected_box = None
    return jsonify({"status": "not_found"})


@app.route("/get_movement")
def get_movement():
    return jsonify({"movement": _movement})


@app.route("/deselect", methods=["POST"])
def deselect():
    global _selected_box
    _selected_box = None
    _send_cmd("S")
    return jsonify({"status": "deselected"})


# ── Cleanup ───────────────────────────────────────────────────────────────────

def _cleanup():
    if _camera:
        _camera.stop()
    if _arduino:
        _arduino.close()


atexit.register(_cleanup)

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _init_hw()
    t = threading.Thread(target=_detect_loop, daemon=True)
    t.start()
    app.run(host=HUMAN_FOLLOW_HOST, port=HUMAN_FOLLOW_PORT,
            debug=False, use_reloader=False)
