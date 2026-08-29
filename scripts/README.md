# scripts/ — Standalone Utility & Test Scripts

These are **self-contained scripts** used during development and testing.
They are **not** part of the main packaged application — for the production
pipeline see the parent packages (`detection/`, `gps/`, `map_server/`, etc.).

| File | Description |
|------|-------------|
| `road_detect_simple.py` | Basic road-damage detection (no GPS, no DB) |
| `road_detect_with_gps.py` | Road detection + GPS + MySQL save |
| `person_detect_save_db.py` | Person detection + GPS + MySQL save |
| `gps_raw_reader.py` | Print raw NMEA sentences from GPS module |
| `camera_stream_yolo.py` | MJPEG stream of YOLO-annotated frames |
| `person_track_simple.py` | Minimal person-tracking Flask server |
| `tracking_simple.py` | Headless person tracking (no web server) |
| `yolo_camera_test.py` | Quick camera + YOLO sanity check |
| `hello_test.py` | Basic test file |

> **Tip:** Run any script directly from the project root, e.g.:
> ```bash
> python scripts/yolo_camera_test.py
> ```
