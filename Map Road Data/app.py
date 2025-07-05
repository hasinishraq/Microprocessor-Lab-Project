import atexit
import signal
import mysql.connector  # Use mysql-connector instead of MySQLdb
from flask import Flask, render_template
import folium
from folium import CustomIcon

app = Flask(__name__)

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'hasin'
DB_PASSWORD = '12345678'
DB_NAME = 'road'

# Function to establish the database connection using mysql-connector
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# Function to get data from the database
def get_data_from_db():
    db = None
    try:
        # Establish the connection
        db = get_db_connection()
        cursor = db.cursor()
        
        # Query to get the coordinates and type from the detected_road_conditions table
        cursor.execute("SELECT latitude, longitude, name FROM detected_road_conditions")
        data = cursor.fetchall()
        
        return data
    except Exception as e:
        print(f"Error occurred: {e}")
        return []
    finally:
        # Cleanup: Ensure the connection is always closed
        if db:
            db.close()

# Function to create the map with markers
def create_map():
    # Create a folium map centered around a default latitude and longitude
    folium_map = folium.Map(location=[23.8103, 90.4125], zoom_start=12)  # Default to Dhaka's lat, long
    
    # Get data from the database
    features = get_data_from_db()
    
    # Add markers based on the type
    for feature in features:
        lat, lon, feature_type = feature
        if feature_type == 'Potholes':
            # Use custom icon for potholes (place the image in the static/icons directory)
            icon = CustomIcon(icon_image='/static/icons/pothole_icon.png', icon_size=(30, 30))  # Customize size
        elif feature_type == 'Crack':
            # Use custom icon for cracks (place the image in the static/icons directory)
            icon = CustomIcon(icon_image='/static/icons/crack_icon.png', icon_size=(30, 30))  # Customize size
        else:
            # Default icon for other road conditions
            icon = folium.Icon(color='green', icon='check', prefix='fa')  # Green for road
        
        folium.Marker([lat, lon], icon=icon, popup=f'{feature_type.capitalize()}').add_to(folium_map)

    return folium_map

@app.route('/')
def index():
    # Generate the map with markers
    folium_map = create_map()

    # Save map to HTML
    map_html = folium_map._repr_html_()
    return render_template('index.html', map_html=map_html)

# Graceful Shutdown Cleanup
def shutdown_cleanup():
    """Gracefully handle cleanup on shutdown."""
    print("? Server is shutting down...")

# Register cleanup function when the server shuts down
atexit.register(shutdown_cleanup)

# Gracefully shutdown the Flask server on receiving SIGINT (Ctrl+C)
def shutdown_server(signal, frame):
    print("? Gracefully shutting down the server...")
    shutdown_cleanup()
    sys.exit(0)

# Register SIGINT (Ctrl+C) signal handler for graceful shutdown
signal.signal(signal.SIGINT, shutdown_server)

if __name__ == '__main__':
    # Run the Flask app, use `use_reloader=False` to prevent restarting Flask server on code changes
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)