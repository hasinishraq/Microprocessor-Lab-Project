# map_server/variants/ — Historical Map Server Variants

These are **earlier iterations** of the map server, preserved for reference.
The **current production server** is `map_server/app.py`.

| File | Origin | Description |
|------|--------|-------------|
| `gps_live_map.py` | `Follium/` | Live GPS tracking map (no detections) |
| `gps_live_map_template.html` | `Follium/templates/` | Template for gps_live_map.py |
| `gps_ai_stream.py` | `GPS AND AI/` | GPS + YOLO detection + camera stream combined |
| `gps_ai_stream_template.html` | `GPS AND AI/templates/` | Template for gps_ai_stream.py |
| `road_data_map.py` | `Map Road Data/` | Map viewer for stored road-damage DB records |
| `road_data_map_template.html` | `Map Road Data/templates/` | Template for road_data_map.py |
| `early_prototype_map.py` | `hhhh/` | Earliest map prototype (uses `features` table) |
| `early_prototype_template.html` | `hhhh/templates/` | Template for early_prototype_map.py |
