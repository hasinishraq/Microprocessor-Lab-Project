import serial
import time

# Open the serial port (adjust to /dev/serial0 based on your results)
ser = serial.Serial('/dev/ttyACM1', baudrate=9600, timeout=1)

try:
    while True:
        # Read a line of raw GPS data
        data = ser.readline()
        if data:
            print(data.decode('utf-8').strip())  # Decode and print the raw NMEA data

        time.sleep(1)  # Delay to avoid overwhelming the output

except KeyboardInterrupt:
    print("Program exited.")
except Exception as e:
    print(f"Error: {e}")
