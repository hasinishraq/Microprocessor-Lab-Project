"""
sensors/accelerometer.py
------------------------
MPU-6050 accelerometer reader via I2C (smbus2).
Used as a secondary bump / pothole detector based on sudden Z-axis spikes.

Hardware
--------
MPU-6050  →  Raspberry Pi 4
VCC       →  3.3 V  (Pin 1)
GND       →  GND    (Pin 6)
SCL       →  SCL    (Pin 5 / GPIO 3)
SDA       →  SDA    (Pin 3 / GPIO 2)
AD0       →  GND    (I²C address 0x68)
"""

import time
import threading
import math

try:
    import smbus2
    _SMBUS_AVAILABLE = True
except ImportError:
    _SMBUS_AVAILABLE = False
    print("[Accel] smbus2 not installed – running in simulation mode.")

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.settings import ACCEL_I2C_ADDRESS, ACCEL_BUMP_THRESHOLD


# ── MPU-6050 Register Map ─────────────────────────────────────────────────────
_REG_PWR_MGMT_1   = 0x6B
_REG_ACCEL_XOUT_H = 0x3B
_ACCEL_SENSITIVITY = 16384.0   # LSB/g for ±2 g range (default)


class AccelerometerReader:
    """
    Reads X, Y, Z acceleration from MPU-6050 and detects road bumps.

    Usage
    -----
    accel = AccelerometerReader()
    accel.start()
    ax, ay, az = accel.get_accel()    # in g-units
    if accel.bump_detected():
        ...
    """

    def __init__(self, i2c_address: int = ACCEL_I2C_ADDRESS,
                 bump_threshold: float = ACCEL_BUMP_THRESHOLD):
        self.address        = i2c_address
        self.bump_threshold = bump_threshold
        self._ax = self._ay = self._az = 0.0
        self._bump     = False
        self._lock     = threading.Lock()
        self._running  = False
        self._bus      = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Initialise the sensor and begin background polling."""
        if not _SMBUS_AVAILABLE:
            print("[Accel] smbus2 unavailable – accelerometer disabled.")
            return
        try:
            self._bus = smbus2.SMBus(1)        # I2C bus 1 on RPi
            # Wake the MPU-6050 (clear sleep bit)
            self._bus.write_byte_data(self.address, _REG_PWR_MGMT_1, 0x00)
            self._running = True
            t = threading.Thread(target=self._poll_loop, daemon=True)
            t.start()
            print(f"[Accel] MPU-6050 started at I2C 0x{self.address:02X}")
        except Exception as exc:
            print(f"[Accel] Init error: {exc}")

    def stop(self) -> None:
        self._running = False

    def get_accel(self) -> tuple:
        """Return (ax, ay, az) in g-units."""
        with self._lock:
            return self._ax, self._ay, self._az

    def bump_detected(self) -> bool:
        """Return True if a bump was detected since the last call, then reset."""
        with self._lock:
            flag = self._bump
            self._bump = False
            return flag

    # ── Internal ──────────────────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while self._running:
            try:
                ax, ay, az = self._read_raw()
                magnitude  = math.sqrt(ax**2 + ay**2 + az**2)
                with self._lock:
                    self._ax, self._ay, self._az = ax, ay, az
                    if magnitude > self.bump_threshold:
                        self._bump = True
                        print(f"[Accel] Bump! |a|={magnitude:.2f} g")
            except Exception as exc:
                print(f"[Accel] Read error: {exc}")
            time.sleep(0.05)   # 20 Hz

    def _read_raw(self) -> tuple:
        """Read 6 bytes from the accelerometer registers and convert to g."""
        data = self._bus.read_i2c_block_data(self.address, _REG_ACCEL_XOUT_H, 6)
        ax = self._to_signed(data[0] << 8 | data[1]) / _ACCEL_SENSITIVITY
        ay = self._to_signed(data[2] << 8 | data[3]) / _ACCEL_SENSITIVITY
        az = self._to_signed(data[4] << 8 | data[5]) / _ACCEL_SENSITIVITY
        return ax, ay, az

    @staticmethod
    def _to_signed(value: int) -> int:
        """Convert unsigned 16-bit integer to signed."""
        return value - 65536 if value >= 32768 else value


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    accel = AccelerometerReader()
    accel.start()
    print("Reading accelerometer… (Ctrl+C to stop)")
    try:
        while True:
            ax, ay, az = accel.get_accel()
            print(f"  ax={ax:+.3f}g  ay={ay:+.3f}g  az={az:+.3f}g")
            if accel.bump_detected():
                print("  ⚠ Bump / Pothole detected by accelerometer!")
            time.sleep(0.5)
    except KeyboardInterrupt:
        accel.stop()
        print("Stopped.")
