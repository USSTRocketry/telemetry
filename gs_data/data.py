from multiprocessing import Process, Queue
from common.redis_helper import RedisHelper, TelemetryKeys
from .radio import RFM95Radio
import board
import struct
import time

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
    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.redis_helper = RedisHelper(flight_name=FLIGHT)

        # default SPI bus (SPI0) 
        #   SCLK = GPIO11 (Pin 23)
        #   MOSI = GPIO10 (Pin 19)
        #   MISO = GPIO9 (Pin 21)
        spi = board.SPI() 

        self.radio = RFM95Radio(spi=spi, cs_pin=board.D17, reset_pin=board.D27, frequency=915.0, baudrate=4000000, node=1)

        self._db_str = ""
    
    def receive(self):
        data = self.radio.receive()
        while data is None:
            data = self.radio.receive()
        
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
        else:
            print("Failed to unpack telemetry data")
        
    def db_str(self):
        return self._db_str

    def run(self):
        while True:
            self.receive()
            time.sleep(0.2)

