import redis
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import threading

# Initialize Redis connection with error handling
try:
    redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
except redis.ConnectionError as e:
    print("Failed to connect to Redis:", e)
    exit(1)

# Function to fetch sensor data from Redis
def fetch_sensor_data(sensor_keys):
    sensor_data = {}
    for key in sensor_keys:
        try:
            values = redis_client.lrange(key, 0, -1)
            sensor_data[key] = [float(v) for v in values]
        except (redis.ResponseError, ValueError) as e:
            print(f"Error fetching or parsing data for {key}: {e}")
            sensor_data[key] = []
    return sensor_data

# Real-time plotting with Matplotlib
fig, axs = plt.subplots(3, 3, figsize=(14, 8))
axs = axs.flatten()

# Dynamic sensor list and colors
sensor_keys = ["Accelerometer_X", "Accelerometer_Y", "Accelerometer_Z", "Barometer"]
colors = ["#ff5555", "#55ff55", "#5555ff", "#ffaa00"]

# Initialize plot data containers
plot_data = {key: [] for key in sensor_keys}
last_data_length = {key: 0 for key in sensor_keys}

# Initialize empty plots
for ax, sensor, color in zip(axs, sensor_keys, colors):
    ax.set_title(sensor, fontsize=10, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(-1000, 1000)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.plot([], [], color=color, label=sensor)
    ax.legend(loc="upper right")

def update(frame):
    sensor_data = fetch_sensor_data(sensor_keys)
    for i, (ax, sensor, color) in enumerate(zip(axs, sensor_keys, colors)):
        if sensor in sensor_data:
            new_data = sensor_data[sensor][last_data_length[sensor]:]
            plot_data[sensor].extend(new_data)
            last_data_length[sensor] += len(new_data)

            ax.cla()
            ax.set_title(sensor, fontsize=10, fontweight="bold")
            ax.set_xlim(max(0, len(plot_data[sensor]) - 100), len(plot_data[sensor]))
            ax.set_ylim(-1000, 1000)  # Adjust dynamically if needed
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.plot(plot_data[sensor], color=color, label=sensor)
            ax.legend(loc="upper right")

# Dynamic grid adjustment
def adjust_grid():
    num_sensors = len(sensor_keys)
    rows = (num_sensors + 2) // 3
    cols = min(num_sensors, 3)
    global fig, axs
    fig.clear()
    axs = fig.subplots(rows, cols).flatten()
    spacing = max(0.2, 0.8 / rows)  # Adjust spacing dynamically based on rows
    plt.subplots_adjust(hspace=spacing, wspace=spacing)

# Real-time clock display
def update_clock():
    while True:
        plt.suptitle(time.strftime("%H:%M:%S"), fontsize=16, fontweight="bold")
        time.sleep(1)

clock_thread = threading.Thread(target=update_clock, daemon=True)
clock_thread.start()

ani = FuncAnimation(fig, update, interval=100, cache_frame_data=False)

plt.show()
