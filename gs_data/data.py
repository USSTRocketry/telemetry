import json
import os
import csv
import uuid
from multiprocessing import Process, Queue
from datetime import datetime
from common.redis_helper import RedisHelper, TelemetryKeys
from .radio import RFM95Radio
import board
import struct
import time
from enum import Enum


TASKS_KEY = "gs:tasks"

class PacketType(Enum):
    PING = 1
    ACK_PONG = 2
    SENSOR_DATA = 3
    COMMAND = 4

class NetworkCommands(Enum):
    ENABLE_DEBUGGING = 1
    FLIGHT_READY = 2
    SWITCH_RADIO_FREQUENCY = 3



FLIGHT = "TEST01"

"""
+--------------------+-----------+-------+------------+-------------------------------+
| Field              | Type      | Bytes | Multiplier | Description                   |
+--------------------+-----------+-------+------------+-------------------------------+
| BMP280 Temp        | int16_t   | 2     | *100       | Temperature in °C             |
| Pressure           | uint32_t  | 4     | *100       | Pressure in hPa               |
| BMP280 Altitude    | int16_t   | 2     | *10        | Altitude in meters            |
| Accel X/Y/Z        | int16_t*3 | 6     | *100       | Acceleration in m/s²          |
| Gyro X/Y/Z         | int16_t*3 | 6     | *100       | Angular velocity in °/s       |
| IMU Temp           | int16_t   | 2     | *100       | IMU temperature in °C         |
| Mag X/Y/Z          | int16_t*3 | 6     | *100       | Magnetic field in µT          |
| Extra Temp Sensor  | int16_t   | 2     | *100       | External temp in °C           |
| GPS Latitude       | int32_t   | 4     | *1e7       | Degrees                       |
| GPS Longitude      | int32_t   | 4     | *1e7       | Degrees                       |
| GPS Altitude       | int16_t   | 2     | *10        | Altitude in meters            |
| GPS Speed          | uint16_t  | 2     | *100       | Speed in knots                |
| GPS Angle          | uint16_t  | 2     | *100       | Heading angle in degrees      |
| timestamp          | uint32_t  | 4     | *1         | Timestamp of data             |
+--------------------+-----------+-------+------------+-------------------------------+
| TOTAL              |           | 54    |            |                               |
+--------------------+-----------+-------+------------+-------------------------------+

"""

# Define the format string for struct.unpack
FORMAT = "<h I h 3h 3h h 3h h i i h H H I"

class TelemetryData:
    def __init__(self):
        self.bmp280_temp = 0
        self.bmp280_pressure = 0
        self.bmp280_altitude = 0
        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0
        self.imu_temp = 0
        self.mag_x = 0
        self.mag_y = 0
        self.mag_z = 0
        self.extra_temp_sensor = 0
        self.gps_latitude = 0
        self.gps_longitude = 0
        self.gps_altitude = 0
        self.gps_speed = 0
        self.gps_angle = 0
        self.timestamp = 0
    
    def unpack(self, data: str):
        """
        Unpack the data string into the TelemetryData object.
        """
        try:
            unpacked_data = struct.unpack(FORMAT, data)
            (self.bmp280_temp,
             self.bmp280_pressure,
             self.bmp280_altitude,
             self.accel_x,
             self.accel_y,
             self.accel_z,
             self.gyro_x,
             self.gyro_y,
             self.gyro_z,
             self.imu_temp,
             self.mag_x,
             self.mag_y,
             self.mag_z,
             self.extra_temp_sensor,
             self.gps_latitude,
             self.gps_longitude,
             self.gps_altitude,
             self.gps_speed,
             self.gps_angle,
             self.timestamp) = unpacked_data
            
            # Convert to appropriate units
            self.bmp280_temp = int(self.bmp280_temp)/100
            self.bmp280_pressure = int(self.bmp280_pressure)/100
            self.bmp280_altitude = int(self.bmp280_altitude)/10
            self.accel_x = int(self.accel_x)/100
            self.accel_y = int(self.accel_y)/100
            self.accel_z = int(self.accel_z)/100
            self.gyro_x = int(self.gyro_x)/100
            self.gyro_y = int(self.gyro_y)/100
            self.gyro_z = int(self.gyro_z)/100
            self.imu_temp = int(self.imu_temp)/100
            self.mag_x = int(self.mag_x)/100
            self.mag_y = int(self.mag_y)/100
            self.mag_z = int(self.mag_z)/100
            self.extra_temp_sensor /= 100
            self.gps_latitude = int(self.gps_latitude)/1e7
            self.gps_longitude = int(self.gps_longitude)/1e7
            self.gps_altitude = int(self.gps_altitude)/10
            self.gps_speed = int(self.gps_speed)/100
            self.gps_angle = int(self.gps_angle)/100
            self.timestamp = int(self.timestamp)
            
            return True
        except struct.error as e:
            print(f"Error unpacking data: {e}")
        except ValueError as e:
            print(f"Error converting data: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        return False

    
    def __str__(self):
        return (f"TelemetryData:"
                f"  bmp280_temp:        {self.bmp280_temp}"
                f"  bmp280_pressure:    {self.bmp280_pressure}"
                f"  bmp280_altitude:    {self.bmp280_altitude}"
                f"  accel_x:            {self.accel_x}"
                f"  accel_y:            {self.accel_y}"
                f"  accel_z:            {self.accel_z}"
                f"  gyro_x:             {self.gyro_x}"
                f"  gyro_y:             {self.gyro_y}"
                f"  gyro_z:             {self.gyro_z}"
                f"  imu_temp:           {self.imu_temp}"
                f"  mag_x:              {self.mag_x}"
                f"  mag_y:              {self.mag_y}"
                f"  mag_z:              {self.mag_z}"
                f"  extra_temp_sensor:  {self.extra_temp_sensor}"
                f"  gps_latitude:       {self.gps_latitude}"
                f"  gps_longitude:      {self.gps_longitude}"
                f"  gps_altitude:       {self.gps_altitude}"
                f"  gps_speed:          {self.gps_speed}"
                f"  gps_angle:          {self.gps_angle}"
                f"  timestamp:          {self.timestamp}")



class TelemetryDataProcess(Process):
    def __init__(self, flight_name=FLIGHT):
        super().__init__()
        self.queue = Queue()
        self.redis_helper = RedisHelper(flight_name=flight_name)
        self.redis_helper.init_keys()


        # default SPI bus (SPI0) 
        #   SCLK = GPIO11 (Pin 23)
        #   MOSI = GPIO10 (Pin 19)
        #   MISO = GPIO9 (Pin 21)
        spi = board.SPI() 

        self.radio = RFM95Radio(spi=spi, cs_pin=board.D17, reset_pin=board.D27, 
                                frequency=915, baudrate=4000000, node=100)
        
        # CSV logging setup
        self.telemetry_dir = "/home/rpi/Data"
        os.makedirs(self.telemetry_dir, exist_ok=True)
        start_time = datetime.now().strftime("%Y%m%dT%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        self.csv_filename = f"{flight_name}_{start_time}_{unique_id}.csv"
        self.csv_path = os.path.join(self.telemetry_dir, self.csv_filename)
        self.csv_file = open(self.csv_path, "a", newline="")
        self.csv_writer = None
        self.csv_headers = [
            "bmp280_temp", "bmp280_pressure", "bmp280_altitude",
            "accel_x", "accel_y", "accel_z",
            "gyro_x", "gyro_y", "gyro_z",
            "imu_temp", "mag_x", "mag_y", "mag_z",
            "extra_temp_sensor", "gps_latitude", "gps_longitude",
            "gps_altitude", "gps_speed", "gps_angle", "timestamp"
        ]
        # Write headers if file is new
        if os.stat(self.csv_path).st_size == 0:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.csv_headers)
            self.csv_writer.writeheader()
            self.csv_file.flush()
        else:
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.csv_headers)

        self._db_str = ""
    
    def receive(self):
        data = self.radio.receive()
        if data is None:
            return None
        
        if len(data) > 0:
            return data
        else:
            return None
    
    def handle_command(self, command):
        pass

    def handle_telemetry(self, data):
        # Decode the data, convert back to floating point and construct TelemetryData
        telemetry_data = TelemetryData()
        if telemetry_data.unpack(data):
            self._db_str = str(telemetry_data)
            self.redis_helper.ts_append(TelemetryKeys.BMP280_TEMP, telemetry_data.bmp280_temp)
            self.redis_helper.ts_append(TelemetryKeys.BMP280_PRESSURE, telemetry_data.bmp280_pressure)
            self.redis_helper.ts_append(TelemetryKeys.BMP280_ALTITUDE, telemetry_data.bmp280_altitude)
            self.redis_helper.ts_append(TelemetryKeys.ACCEL_X, telemetry_data.accel_x)
            self.redis_helper.ts_append(TelemetryKeys.ACCEL_Y, telemetry_data.accel_y)
            self.redis_helper.ts_append(TelemetryKeys.ACCEL_Z, telemetry_data.accel_z)
            self.redis_helper.ts_append(TelemetryKeys.GYRO_X, telemetry_data.gyro_x)
            self.redis_helper.ts_append(TelemetryKeys.GYRO_Y, telemetry_data.gyro_y)
            self.redis_helper.ts_append(TelemetryKeys.GYRO_Z, telemetry_data.gyro_z)
            self.redis_helper.ts_append(TelemetryKeys.ACCEL_TEMP, telemetry_data.imu_temp)
            self.redis_helper.ts_append(TelemetryKeys.MAG_X, telemetry_data.mag_x)
            self.redis_helper.ts_append(TelemetryKeys.MAG_Y, telemetry_data.mag_y)
            self.redis_helper.ts_append(TelemetryKeys.MAG_Z, telemetry_data.mag_z)
            self.redis_helper.ts_append(TelemetryKeys.TEMP_SENSOR, telemetry_data.extra_temp_sensor)
            self.redis_helper.ts_append(TelemetryKeys.GPS_LATITUDE, telemetry_data.gps_latitude)
            self.redis_helper.ts_append(TelemetryKeys.GPS_LONGITUDE, telemetry_data.gps_longitude)
            self.redis_helper.ts_append(TelemetryKeys.GPS_ALTITUDE, telemetry_data.gps_altitude)
            self.redis_helper.ts_append(TelemetryKeys.GPS_SPEED, telemetry_data.gps_speed)
            self.redis_helper.ts_append(TelemetryKeys.GPS_ANGLE, telemetry_data.gps_angle)
            self.redis_helper.ts_append(TelemetryKeys.TIMESTAMP, telemetry_data.timestamp)
            # CSV logging
            try:
                row = {k: getattr(telemetry_data, k) for k in self.csv_headers}
                self.csv_writer.writerow(row)
                self.csv_file.flush()
                os.fsync(self.csv_file.fileno())
            except Exception as e:
                print(f"[CSV ERROR] {e}")
        else:
            print("Failed to unpack telemetry data")
        
    def db_str(self):
        return self._db_str
    
    def perform_frequency_change(self, frequency):
        """
        Protocol Flow:
        1. Peripheral receives a message from the ground station: 
            Format: [COMMAND, SWITCH_RADIO_FREQUENCY, <float frequency in MHz>]
        2. Validates the message format and extracts the desired frequency.
        3. Sends an acknowledgment echoing the same command and frequency back to the ground station.
        4. Waits for up to 3 seconds to receive a final "Ack" from the ground station confirming the switch.
        5. If acknowledgment is received within timeout:
            - Applies the new frequency to the radio.
        6. If not acknowledged in time:
            - Aborts the procedure; frequency remains unchanged.

        Ground Station Responsibilities:
            - Send initial command with target frequency.
            - Wait for peripheral's echo response (3 second timeout).
            - Respond with final acknowledgment only if echo is correct.
            - Switch local frequency only after sending acknowledgment.
        """

        packet = struct.pack("<BBf",
                             PacketType.COMMAND.value,
                             NetworkCommands.SWITCH_RADIO_FREQUENCY.value,
                             frequency)
        self.radio.send(packet)
        # Wait for ACK. 3 seconds timeout
        cur_time = time.time()
        print(f"sent frequency change command [{packet}]. Waiting for ACK")
        while time.time() - cur_time < 3:
            ack = self.receive()
            if ack is not None:
                print("Potential ACK received. Checking...")
            if ack is not None and len(ack) == 6:
                # Check if the command matches
                if ack[0] == PacketType.ACK_PONG.value \
                    and ack[1] == NetworkCommands.SWITCH_RADIO_FREQUENCY.value:
                    # Extract frequency from the response
                    received_freq = struct.unpack("<f", ack[2:])[0]
                    if received_freq == frequency:
                        print(f"Frequency switch confirmed to {frequency} MHz")
                        # send ack
                        packet = struct.pack("<BB",
                             PacketType.ACK_PONG.value,
                             NetworkCommands.SWITCH_RADIO_FREQUENCY.value)
                        self.radio.send(packet)
                        self.radio.set_frequency(frequency)
                        return True
                    else:
                        print(f"Frequency mismatch: expected {frequency}, got {received_freq}")
                        return False
        print("No acknowledgment received within timeout. Frequency switch aborted.")
        return False
    
    def handle_task(self, task):
        task_id = task["task_id"]
        task_type = task["task"]
        params = task.get("params", {})
        
        print(f"Got Task: {task}")
        try:
            if task_type == "change_frequency":
                freq = params["frequency"]
                # sanity check
                if not (900 <= freq <= 930):
                    raise ValueError("Frequency must be between 900 MHz and 930 MHz")
                res = self.perform_frequency_change(freq)
                if res:
                    result = f"Frequency change to {freq} MHz completed"
                    self.redis_helper.set("frequency", freq)
                else:
                    result = f"Frequency change to {freq} MHz failed"
            elif task_type == "force_ground_frequency":
                freq = params["frequency"]
                # sanity check
                if not (900 <= freq <= 930):
                    raise ValueError("Frequency must be between 900 MHz and 930 MHz")
                self.radio.set_frequency(freq)
                self.redis_helper.set("frequency", freq)
                result = f"Local frequency set to {freq} MHz"
            elif task_type == "send_flight_ready":
                result = "TODO: Flight ready command sent"
            elif task_type == "set_ground_station_id":
                result = f"TODO: Ground station ID set to {params['id']}"
            elif task_type == "set_rocket_id":
                result = f"TODO: Rocket ID set to {params['id']}"
            else:
                result = f"Unknown task: {task_type}"
        except Exception as e:
            result = f"[ERROR] {str(e)}"

        self.redis_helper.redis.set(f"gs:response:{task_id}", result, ex=10)


    def run(self):
        try:
            while True:
                data = self.receive()
                if data is not None:
                    pkt_type = data[0]
                    if pkt_type == PacketType.SENSOR_DATA.value:
                        telemetry = data[1:]
                        self.handle_telemetry(telemetry)
                    elif pkt_type == PacketType.COMMAND.value:
                        command = data[1:]
                        self.handle_command(command)
                    else:
                        print(f"Invalid packet type: {pkt_type}")
                # Check for tasks in the queue
                task_json = self.redis_helper.redis.lpop(TASKS_KEY)
                if task_json:
                    try:
                        task = json.loads(task_json)
                        self.handle_task(task)
                    except Exception as e:
                        print(f"[TASK ERROR] {e}")
                time.sleep(0.2)
        finally:
            try:
                self.csv_file.close()
            except Exception:
                pass

