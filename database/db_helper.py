"""
database/db_helper.py
---------------------
MySQL helper for storing and retrieving road-damage detections.
"""

import mysql.connector
import threading
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_TABLE


class DBHelper:
    """
    Thread-safe MySQL helper.

    Usage
    -----
    db = DBHelper()
    db.connect()
    db.insert_detection("Pothole", 23.8103, 90.4125)
    rows = db.fetch_all_detections()
    db.close()
    """

    def __init__(self):
        self._conn   = None
        self._cursor = None
        self._lock   = threading.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open the database connection. Returns True on success."""
        try:
            self._conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
            self._cursor = self._conn.cursor()
            print(f"[DB] Connected to '{DB_NAME}' on {DB_HOST}")
            return True
        except mysql.connector.Error as exc:
            print(f"[DB] Connection failed: {exc}")
            return False

    def close(self) -> None:
        """Close cursor and connection."""
        try:
            if self._cursor:
                self._cursor.close()
            if self._conn and self._conn.is_connected():
                self._conn.close()
            print("[DB] Connection closed.")
        except Exception as exc:
            print(f"[DB] Error closing connection: {exc}")

    # ── Write ─────────────────────────────────────────────────────────────────

    def insert_detection(self, name: str, latitude: float, longitude: float,
                         confidence: float = None, source: str = "vision") -> bool:
        """
        Insert one road-damage detection record.

        Parameters
        ----------
        name        : 'Pothole' | 'Crack' | etc.
        latitude    : decimal degrees
        longitude   : decimal degrees
        confidence  : YOLO confidence score (0–1), optional
        source      : 'vision' | 'accelerometer' | 'combined'
        """
        sql = (
            f"INSERT INTO {DB_TABLE} "
            "(name, latitude, longitude, confidence, source) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        values = (name, latitude, longitude, confidence, source)
        try:
            with self._lock:
                self._cursor.execute(sql, values)
                self._conn.commit()
            print(f"[DB] Saved: {name} @ ({latitude:.6f}, {longitude:.6f})  "
                  f"conf={confidence}  src={source}")
            return True
        except Exception as exc:
            print(f"[DB] Insert error: {exc}")
            return False

    # ── Read ──────────────────────────────────────────────────────────────────

    def fetch_all_detections(self) -> list:
        """
        Return all detection rows as a list of dicts:
        [{'id', 'name', 'latitude', 'longitude', 'confidence',
          'source', 'detected_at'}, ...]
        """
        sql = (
            f"SELECT id, name, latitude, longitude, confidence, "
            f"source, detected_at FROM {DB_TABLE} ORDER BY detected_at DESC"
        )
        try:
            with self._lock:
                self._cursor.execute(sql)
                rows = self._cursor.fetchall()
            keys = ["id", "name", "latitude", "longitude",
                    "confidence", "source", "detected_at"]
            return [dict(zip(keys, row)) for row in rows]
        except Exception as exc:
            print(f"[DB] Fetch error: {exc}")
            return []

    def fetch_recent(self, limit: int = 100) -> list:
        """Return the most recent N detections."""
        sql = (
            f"SELECT id, name, latitude, longitude, confidence, "
            f"source, detected_at FROM {DB_TABLE} "
            f"ORDER BY detected_at DESC LIMIT %s"
        )
        try:
            with self._lock:
                self._cursor.execute(sql, (limit,))
                rows = self._cursor.fetchall()
            keys = ["id", "name", "latitude", "longitude",
                    "confidence", "source", "detected_at"]
            return [dict(zip(keys, row)) for row in rows]
        except Exception as exc:
            print(f"[DB] Fetch error: {exc}")
            return []
