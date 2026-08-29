"""
gps/parser.py
-------------
NMEA sentence parser and serial reader for the GPS module.
Supports $GPGGA and $GPRMC sentences.
"""

import threading
import time
import serial
import sys
import os

# Allow running standalone or as part of the package
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import GPS_PORT, GPS_BAUDRATE


class GPSReader:
    """
    Thread-safe GPS reader.

    Usage
    -----
    gps = GPSReader()
    gps.start()                 # spawns background thread
    lat, lon = gps.get_coords() # returns (None, None) until fix
    """

    def __init__(self, port: str = GPS_PORT, baudrate: int = GPS_BAUDRATE):
        self.port     = port
        self.baudrate = baudrate
        self._lat     = None
        self._lon     = None
        self._lock    = threading.Lock()
        self._running = False
        self._thread  = None
        self._ser     = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Open the serial port and begin reading in a daemon thread."""
        try:
            self._ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print(f"[GPS] Reader started on {self.port} @ {self.baudrate} baud")
        except serial.SerialException as exc:
            print(f"[GPS] ERROR: Could not open {self.port}: {exc}")

    def stop(self) -> None:
        """Stop the background reader and close the serial port."""
        self._running = False
        if self._ser and self._ser.is_open:
            self._ser.close()

    def get_coords(self) -> tuple:
        """Return the latest (latitude, longitude) tuple, or (None, None)."""
        with self._lock:
            return self._lat, self._lon

    def has_fix(self) -> bool:
        """Return True once valid coordinates have been received."""
        lat, lon = self.get_coords()
        return lat is not None and lon is not None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _read_loop(self) -> None:
        """Background loop: read lines from serial and parse them."""
        while self._running:
            try:
                raw = self._ser.readline()
                if raw:
                    sentence = raw.decode("utf-8", errors="ignore").strip()
                    self._parse(sentence)
            except Exception as exc:
                print(f"[GPS] Read error: {exc}")
            time.sleep(0.1)

    def _parse(self, sentence: str) -> None:
        """Dispatch NMEA sentence to the appropriate handler."""
        if sentence.startswith("$GPGGA") or sentence.startswith("$GNGGA"):
            self._parse_gpgga(sentence)
        elif sentence.startswith("$GPRMC") or sentence.startswith("$GNRMC"):
            self._parse_gprmc(sentence)

    def _parse_gpgga(self, sentence: str) -> None:
        """
        Parse $GPGGA sentence.
        Field layout: $GPGGA,time,lat,N/S,lon,E/W,fix,sats,hdop,alt,...
        """
        try:
            parts = sentence.split(",")
            if len(parts) < 6 or not parts[2] or not parts[4]:
                return

            lat = self._nmea_to_decimal(parts[2], parts[3])
            lon = self._nmea_to_decimal(parts[4], parts[5])

            with self._lock:
                self._lat = lat
                self._lon = lon

            print(f"[GPS] Fix: {lat:.6f}, {lon:.6f}  (GPGGA)")
        except Exception as exc:
            print(f"[GPS] GPGGA parse error: {exc}")

    def _parse_gprmc(self, sentence: str) -> None:
        """
        Parse $GPRMC sentence.
        Field layout: $GPRMC,time,status,lat,N/S,lon,E/W,...
        """
        try:
            parts = sentence.split(",")
            if len(parts) < 7 or parts[2] != "A":   # 'A' = active/valid
                return

            lat = self._nmea_to_decimal(parts[3], parts[4])
            lon = self._nmea_to_decimal(parts[5], parts[6])

            with self._lock:
                self._lat = lat
                self._lon = lon

            print(f"[GPS] Fix: {lat:.6f}, {lon:.6f}  (GPRMC)")
        except Exception as exc:
            print(f"[GPS] GPRMC parse error: {exc}")

    @staticmethod
    def _nmea_to_decimal(value: str, direction: str) -> float:
        """Convert NMEA ddmm.mmmm / dddmm.mmmm to decimal degrees."""
        raw   = float(value)
        deg   = int(raw // 100)
        mins  = raw % 100
        decimal = deg + (mins / 60.0)
        if direction in ("S", "W"):
            decimal = -decimal
        return decimal


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    gps = GPSReader()
    gps.start()
    print("Reading GPS data… (Ctrl+C to stop)")
    try:
        while True:
            lat, lon = gps.get_coords()
            if lat is not None:
                print(f"  → Lat: {lat:.6f}  Lon: {lon:.6f}")
            time.sleep(2)
    except KeyboardInterrupt:
        gps.stop()
        print("Stopped.")
