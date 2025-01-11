import redis
import tkinter as tk
from tkinter import ttk
from tkintermapview import TkinterMapView

# Initialize Redis connection
try:
    redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
except redis.ConnectionError as e:
    print("Failed to connect to Redis:", e)
    exit(1)

# Function to fetch GPS coordinates from Redis
def fetch_gps_coordinates():
    try:
        latitude_list = redis_client.lrange("latitude", 0, -1)
        longitude_list = redis_client.lrange("longitude", 0, -1)

        # Get the most recent value from each list
        latitude = latitude_list[-1] if latitude_list else None
        longitude = longitude_list[-1] if longitude_list else None

        return latitude, longitude
    except (redis.ResponseError, IndexError) as e:
        print(f"Error fetching GPS data: {e}")
        return None, None

# Function to update telemetry data
def update_telemetry_data():
    # Example mock telemetry data (replace this with real data fetching from Redis)
    telemetry_label_value.config(text="Telemetry data updated in real-time...")
    # Schedule the next update
    telemetry_tab.after(1000, update_telemetry_data)

# Function to update the map with GPS coordinates
def update_map():
    latitude, longitude = fetch_gps_coordinates()
    if latitude and longitude:
        try:
            lat = float(latitude)
            lon = float(longitude)
            gps_map.set_position(lat, lon)
            gps_map.set_zoom(15)
            gps_map.set_marker(lat, lon, text="Current Location")
        except ValueError as e:
            print(f"Invalid GPS data: {e}")
    else:
        print("No GPS data available.")
    # Schedule the next update
    gps_tab.after(1000, update_map)

# GUI setup
root = tk.Tk()
root.title("Telemetry and GPS GUI")
root.geometry("1000x700")

# Create a notebook for tabs
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# Create the Telemetry tab
telemetry_tab = ttk.Frame(notebook)
notebook.add(telemetry_tab, text="Telemetry Data")

# Telemetry label
telemetry_label = tk.Label(telemetry_tab, text="Telemetry Data", font=("Arial", 16, "bold"))
telemetry_label.pack(pady=10)

telemetry_label_value = tk.Label(telemetry_tab, text="No Data", font=("Arial", 12))
telemetry_label_value.pack(pady=10)

# Create the GPS tab
gps_tab = ttk.Frame(notebook)
notebook.add(gps_tab, text="GPS Map")

# Map display using tkintermapview with Google Maps tiles
gps_map = TkinterMapView(gps_tab, width=800, height=600, corner_radius=0)

# Use this for a google map tile
gps_map.set_tile_server(
    "https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",  # Google Maps Roadmap tiles
    max_zoom=22
)
gps_map.pack(fill="both", expand=True, padx=10, pady=10)

# Start periodic updates for telemetry and GPS data
telemetry_tab.after(1000, update_telemetry_data)  # Start telemetry updates
gps_tab.after(1000, update_map)  # Start GPS map updates

# Start the GUI loop
root.mainloop()
