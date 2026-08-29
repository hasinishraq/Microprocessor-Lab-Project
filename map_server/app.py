"""
map_server/app.py
-----------------
Flask web server that displays an interactive Folium map of all
road-damage detections stored in MySQL.

Endpoints
---------
GET /          → Full map page with markers
GET /api/data  → JSON list of all detections (for AJAX refresh)
GET /api/stats → Summary counts per damage type

Run:
    python map_server/app.py
    Open http://<pi-ip>:5000 in any browser on the same network.
"""

import atexit
import signal
import sys
import os
import json
from datetime import datetime

import folium
from folium.plugins import MarkerCluster
from flask import Flask, render_template, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    MAP_SERVER_HOST, MAP_SERVER_PORT,
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM,
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME,
)
from database.db_helper import DBHelper


app = Flask(__name__)
db  = DBHelper()


# ── Map colours & icons ───────────────────────────────────────────────────────
MARKER_CONFIG = {
    "Pothole":    {"color": "red",    "icon": "exclamation-triangle", "prefix": "fa"},
    "Crack":      {"color": "orange", "icon": "times-circle",         "prefix": "fa"},
    "BumpEvent":  {"color": "blue",   "icon": "bolt",                 "prefix": "fa"},
    "default":    {"color": "gray",   "icon": "question",             "prefix": "fa"},
}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the full map dashboard."""
    detections = db.fetch_all_detections()
    folium_map = _build_map(detections)
    map_html   = folium_map._repr_html_()
    stats      = _compute_stats(detections)
    return render_template("index.html",
                           map_html=map_html,
                           stats=stats,
                           total=len(detections))


@app.route("/api/data")
def api_data():
    """Return all detections as JSON (for live refresh)."""
    rows = db.fetch_all_detections()
    # Make datetimes serialisable
    for r in rows:
        if isinstance(r.get("detected_at"), datetime):
            r["detected_at"] = r["detected_at"].isoformat()
    return jsonify(rows)


@app.route("/api/stats")
def api_stats():
    rows  = db.fetch_all_detections()
    stats = _compute_stats(rows)
    return jsonify(stats)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_map(detections: list) -> folium.Map:
    """Build a Folium map with clustered markers for each detection."""
    centre = [DEFAULT_LAT, DEFAULT_LON]

    # Centre on the most recent fix if available
    for det in detections:
        if det["latitude"] and det["longitude"]:
            centre = [float(det["latitude"]), float(det["longitude"])]
            break

    fmap    = folium.Map(location=centre, zoom_start=DEFAULT_ZOOM,
                         tiles="OpenStreetMap")
    cluster = MarkerCluster(name="Road Damage").add_to(fmap)

    for det in detections:
        lat  = det.get("latitude")
        lon  = det.get("longitude")
        name = det.get("name", "Unknown")

        if lat is None or lon is None:
            continue

        cfg     = MARKER_CONFIG.get(name, MARKER_CONFIG["default"])
        conf    = det.get("confidence")
        conf_str = f"{conf:.0%}" if conf is not None else "N/A"
        ts      = det.get("detected_at", "")
        popup_html = (
            f"<b>{name}</b><br>"
            f"Lat: {float(lat):.6f}<br>"
            f"Lon: {float(lon):.6f}<br>"
            f"Confidence: {conf_str}<br>"
            f"Source: {det.get('source','?')}<br>"
            f"Time: {ts}"
        )

        folium.Marker(
            location=[float(lat), float(lon)],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=cfg["color"],
                             icon=cfg["icon"],
                             prefix=cfg["prefix"]),
            tooltip=name,
        ).add_to(cluster)

    folium.LayerControl().add_to(fmap)
    return fmap


def _compute_stats(detections: list) -> dict:
    stats = {}
    for det in detections:
        name = det.get("name", "Unknown")
        stats[name] = stats.get(name, 0) + 1
    return stats


# ── Graceful shutdown ─────────────────────────────────────────────────────────

def _shutdown(sig=None, frame=None):
    print("\n[MapServer] Shutting down…")
    db.close()
    sys.exit(0)


atexit.register(db.close)
signal.signal(signal.SIGINT, _shutdown)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.connect()
    app.run(host=MAP_SERVER_HOST, port=MAP_SERVER_PORT,
            debug=False, use_reloader=False)
