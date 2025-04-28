import redis

"""Redis Helper Class for Redis Operations"""

""" Sample data
BMP280        - Temperature: 29.61 °C, Pressure: 95519.41 hPa, Altitude: 494.97 m
Accelerometer - X: 0.10 m/s^2, Y: -0.06 m/s^2, Z: 9.94 m/s^2, Gyro X: 0.01 °/s, Y: 0.01 °/s, Z: 0.00 °/s, Temperature: 30.21 °C
Magnetometer  - X: -1.01 µT, Y: -19.83 µT, Z: -18.55 µT
Temp Sensor   - Temperature: 29.44 °C
GPS           - Latitude: 52.13, Longitude: -106.64, Altitude: 219.80 m, Speed: 0.50 knots, Angle: 204.92 °
"""
#------------ Keys -----------------

# BMP280
BMP280_TEMP     = "bmp280.temp"
BMP280_PRESSURE = "bmp280.pressure"
BMP280_ALTITUDE = "bmp280.altitude"

# Accelerometer
ACCEL_X         = "accel.x"
ACCEL_Y         = "accel.y"
ACCEL_Z         = "accel.z"
GYRO_X          = "gyro.x"
GYRO_Y          = "gyro.y"
GYRO_Z          = "gyro.z"
ACCEL_TEMP      = "accel.temp"

# Magnetometer
MAG_X           = "mag.x"
MAG_Y           = "mag.y"
MAG_Z           = "mag.z"

# Temp Sensor
TEMP_SENSOR     = "temp.temp"

# GPS
GPS_LATITUDE    = "gps.latitude"
GPS_LONGITUDE   = "gps.longitude"
GPS_ALTITUDE    = "gps.altitude"
GPS_SPEED       = "gps.speed"
GPS_ANGLE       = "gps.angle"

KEYS = [
    BMP280_TEMP,
    BMP280_PRESSURE,
    BMP280_ALTITUDE,
    ACCEL_X,
    ACCEL_Y,
    ACCEL_Z,
    GYRO_X,
    GYRO_Y,
    GYRO_Z,
    ACCEL_TEMP,
    MAG_X,
    MAG_Y,
    MAG_Z,
    TEMP_SENSOR,
    GPS_LATITUDE,
    GPS_LONGITUDE,
    GPS_ALTITUDE,
    GPS_SPEED,
    GPS_ANGLE
]

class RedisHelper():
    def __init__(self, host='localhost', port=6379, db=0, flight_name="LC2025"):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.redis_ts = self.redis.ts()
        self.flight_name = flight_name
        if self.redis.ping():
            print("Connected to Redis")
            for key in KEYS:
                k = f"{flight_name}.{key}"
                if not self.redis.exists(k):
                    self.redis_ts.create(k, retention_msecs=604800000)  # 7 days retention
        else:
            print("Failed to connect to Redis")
    
    def _key(self, key):
        """
        Helper function to format the key with flight name.
        """
        return f"{self.flight_name}.{key}"

    def set(self, key, value):
        self.redis.set(self._key(key), value)

    def get(self, key):
        return self.redis.get(self._key(key))

    def delete(self, key):
        self.redis.delete(self._key(key))

    def exists(self, key):
        return self.redis.exists(self._key(key))
    
    def ts_append(self, key, value):
        try:
            return self.redis_ts.add(self._key(key), "*", value)
        except redis.exceptions.ResponseError as e:
            print(f"Error appending to timeseries: {e}")
            return None
    def ts_append_with_timestamp(self, key, timestamp, value):
        try:
            return self.redis_ts.add(self._key(key), timestamp, value)
        except redis.exceptions.ResponseError as e:
            print(f"Error appending to timeseries with timestamp: {e}")
            return None
    
    def ts_get_last(self, key):
        try:
            return self.redis_ts.get(self._key(key))
        except redis.exceptions.ResponseError as e:
            print(f"Error fetching last value from timeseries: {e}")
            return None

    def ts_get_last_n(self, key, n):
        try:
            last_n_rev = self.redis_ts.revrange(self._key(key), "-", "+", count=n)
            # Reverse the order to get the last n values in the correct order
            last_n = list(reversed(last_n_rev))
            return last_n
        except redis.exceptions.ResponseError as e:
            print(f"Error fetching last {n} values from timeseries: {e}")
            return None
    
    def ts_get_range(self, key, start_time, end_time):
        try:
            return self.redis_ts.range(self._key(key), start_time, end_time)
        except redis.exceptions.ResponseError as e:
            print(f"Error fetching timeseries data: {e}")
            return None
    
    def ts_get_all(self, key):
        try:
            return self.redis_ts.range(self._key(key), "-", "+")
        except redis.exceptions.ResponseError as e:
            print(f"Error fetching all timeseries data: {e}")
            return None