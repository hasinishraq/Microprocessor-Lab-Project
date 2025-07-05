from flask import Flask, render_template_string
import folium
import serial
import time
import threading

app = Flask(__name__)

# GPS initialization
latitude = None
longitude = None

# Lock to protect shared resource (latitude and longitude)
gps_lock = threading.Lock()

# Open the serial port (adjust to /dev/serial0 based on your results)
ser = serial.Serial('/dev/ttyACM0', baudrate=9600, timeout=1)

def parse_gps_data(data):
    """Parse the NMEA sentence to extract latitude and longitude."""
    global latitude, longitude
    try:
        parts = data.split(",")
        
        # Handle $GPGGA sentence: Global Positioning System Fix Data
        if parts[0] == "$GPGGA":
            # Ensure there are enough parts and check if latitude and longitude are available
            if len(parts) >= 6 and parts[2] and parts[4]:
                lat_deg = float(parts[2]) // 100  # Degrees (before the dot)
                lat_min = float(parts[2]) % 100  # Minutes (after the dot)
                lon_deg = float(parts[4]) // 100  # Degrees (before the dot)
                lon_min = float(parts[4]) % 100  # Minutes (after the dot)
                
                # Convert minutes to decimal degrees
                lat = lat_deg + (lat_min / 60)
                lon = lon_deg + (lon_min / 60)
                
                # Apply direction
                if parts[3] == "S":  # South hemisphere
                    lat = -lat
                if parts[5] == "W":  # West hemisphere
                    lon = -lon

                # Lock the shared resource before updating
                with gps_lock:
                    latitude = lat
                    longitude = lon
                print(f"Latitude: {lat}, Longitude: {lon}")
            else:
                print("Invalid data in $GPGGA sentence (missing latitude or longitude).")
                
    except Exception as e:
        print(f"Error parsing data: {e}")

def read_gps_data():
    """Read and process GPS data indefinitely."""
    try:
        while True:
            data = ser.readline()
            if data:
                decoded_data = data.decode('utf-8').strip()  # Decode the data
                print(f"Raw Data: {decoded_data}")  # Print raw NMEA data
                parse_gps_data(decoded_data)  # Parse the NMEA sentence for GPS info

            time.sleep(1)  # Delay to avoid overwhelming the output
    except KeyboardInterrupt:
        print("GPS reading stopped.")
    except Exception as e:
        print(f"Error: {e}")

@app.route('/')
def index():
    # Check if valid coordinates are available
    if latitude is None or longitude is None:
        return "Waiting for GPS data..."

    # Create a Folium map centered around the GPS coordinates
    m = folium.Map(location=[latitude, longitude], zoom_start=15)

    # Add a marker with the current GPS coordinates
    folium.Marker([latitude, longitude], popup=f"Lat: {latitude}, Lon: {longitude}", icon=folium.Icon(color='blue')).add_to(m)

    # Render the map directly in the response using HTML
    map_html = m._repr_html_()  # Folium's internal method to get HTML of the map
    
    # Return the map HTML inside the Flask response
    return render_template_string("""
        <html>
        <head><title>Live GPS Location</title></head>
        <body>
            <h1>Live GPS Location on Map</h1>
            <p>Your current location:</p>
            {{ map_html|safe }}
        </body>
        </html>
    """, map_html=map_html)

if __name__ == '__main__':
    # Start the GPS data reading in a separate thread
    gps_thread = threading.Thread(target=read_gps_data)
    gps_thread.daemon = True  # Allows the thread to exit when the main program ends
    gps_thread.start()

    # Start the Flask app with external IP access
    app.run(host='0.0.0.0', port=5006, debug=True)
