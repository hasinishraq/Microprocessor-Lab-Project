"""
detection/road_detector.py
--------------------------
Main road-damage detection pipeline.

Integrates:
  • Pi Camera 2  →  live video frames
  • YOLOv8 NCNN  →  pothole / crack detection
  • GPS Reader   →  real-time coordinates
  • Accelerometer→  bump cross-validation
  • MySQL DB     →  persistent storage of every detection event

Run directly on the Raspberry Pi:
    python detection/road_detector.py
"""

import cv2
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config.settings import (
    CAMERA_RESOLUTION, CAMERA_FORMAT,
    ROAD_MODEL_PATH, DETECTION_CLASSES,
)
from gps.parser          import GPSReader
from sensors.accelerometer import AccelerometerReader
from database.db_helper  import DBHelper

try:
    from picamera2     import Picamera2
    from ultralytics   import YOLO
    _HW_AVAILABLE = True
except ImportError:
    _HW_AVAILABLE = False
    print("[Detector] Running in stub mode (picamera2 / ultralytics not installed).")


class RoadDetector:
    """
    Road-damage detection rover.

    Parameters
    ----------
    headless : bool
        If True, do not open a display window (useful for SSH sessions).
    save_interval : float
        Minimum seconds between saving duplicate detections for the same class
        at the same GPS coordinate cluster.
    """

    def __init__(self, headless: bool = False, save_interval: float = 3.0):
        self.headless      = headless
        self.save_interval = save_interval
        self._last_saved   = {}   # {class_name: timestamp}

        # Sub-systems
        self.gps   = GPSReader()
        self.accel = AccelerometerReader()
        self.db    = DBHelper()

        self._camera = None
        self._model  = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Initialise all hardware and start reading threads."""
        print("[Detector] Starting Road Rover Detection Pipeline…")
        self.gps.start()
        self.accel.start()

        if not self.db.connect():
            print("[Detector] WARNING: Database unavailable – detections will NOT be saved.")

        if _HW_AVAILABLE:
            self._init_camera()
            self._init_model()
        else:
            print("[Detector] Hardware not available – entering demo loop.")

    def stop(self) -> None:
        """Gracefully shut down all subsystems."""
        if self._camera:
            self._camera.stop()
        self.gps.stop()
        self.accel.stop()
        self.db.close()
        cv2.destroyAllWindows()
        print("[Detector] Stopped.")

    # ── Main Loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Run the detection loop until 'q' is pressed (or Ctrl-C in headless mode)."""
        self.start()

        if not _HW_AVAILABLE:
            print("[Detector] Demo mode – press Ctrl-C to exit.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            self.stop()
            return

        try:
            while True:
                frame = self._camera.capture_array()

                # ── YOLO Inference ────────────────────────────────────────────
                results        = self._model(frame, verbose=False)
                annotated      = results[0].plot()

                # ── FPS overlay ───────────────────────────────────────────────
                infer_ms = results[0].speed.get("inference", 1)
                fps      = 1000.0 / max(infer_ms, 1)
                self._draw_fps(annotated, fps)

                # ── GPS & Accelerometer state ─────────────────────────────────
                lat, lon = self.gps.get_coords()
                bump     = self.accel.bump_detected()

                # ── Process detections ────────────────────────────────────────
                for box in results[0].boxes:
                    cls_id     = int(box.cls[0])
                    confidence = float(box.conf[0])
                    name       = DETECTION_CLASSES.get(cls_id)

                    if name is None:
                        continue

                    if lat is None or lon is None:
                        print(f"[Detector] {name} detected but no GPS fix yet.")
                        continue

                    source = "combined" if bump else "vision"
                    self._try_save(name, lat, lon, confidence, source)

                # ── Accelerometer-only bump ───────────────────────────────────
                if bump and lat is not None:
                    self._try_save("BumpEvent", lat, lon, None, "accelerometer")

                # ── Display ───────────────────────────────────────────────────
                if not self.headless:
                    cv2.imshow("Road Rover – Detection", annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        except KeyboardInterrupt:
            print("\n[Detector] Interrupted by user.")
        finally:
            self.stop()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _init_camera(self) -> None:
        self._camera = Picamera2()
        cfg = self._camera.create_preview_configuration(
            main={"size": CAMERA_RESOLUTION, "format": CAMERA_FORMAT}
        )
        self._camera.configure(cfg)
        self._camera.start()
        print("[Detector] Camera ready.")

    def _init_model(self) -> None:
        self._model = YOLO(ROAD_MODEL_PATH)
        print(f"[Detector] Model loaded: {ROAD_MODEL_PATH}")

    def _try_save(self, name: str, lat: float, lon: float,
                  conf: float, source: str) -> None:
        """Save a detection, but debounce to avoid flooding the DB."""
        now  = time.time()
        last = self._last_saved.get(name, 0)
        if now - last >= self.save_interval:
            self.db.insert_detection(name, lat, lon, conf, source)
            self._last_saved[name] = now

    @staticmethod
    def _draw_fps(frame, fps: float) -> None:
        font      = cv2.FONT_HERSHEY_SIMPLEX
        text      = f"FPS: {fps:.1f}"
        (tw, th), _ = cv2.getTextSize(text, font, 1, 2)
        x = frame.shape[1] - tw - 10
        y = th + 10
        cv2.putText(frame, text, (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Road Rover – damage detection")
    parser.add_argument("--headless", action="store_true",
                        help="Run without GUI (SSH / no display)")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Minimum seconds between DB saves for same class")
    args = parser.parse_args()

    rover = RoadDetector(headless=args.headless, save_interval=args.interval)
    rover.run()
