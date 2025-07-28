import redis
from typing import Tuple

"""Redis Helper Class for Redis Operations"""

class TelemetryKey():
    def __init__(self, key, labels: dict, unit=None):
        self.key = key
        self.labels = labels
    # return the key if object is referened as a string
    def __str__(self):
        return self.key

class TelemetryKeys:
    """Class to hold telemetry keys for easy access and reuse."""
    
    # BMP280
    BMP280_TEMP     = TelemetryKey(
        "bmp280.temperature",
        {"sensor": "bmp280", "name": "Temperature", "unit": "C"}
    )
    BMP280_PRESSURE = TelemetryKey(
        "bmp280.pressure",
        {"sensor": "bmp280", "name": "Pressure", "unit": "hPa"}
    )
    BMP280_ALTITUDE = TelemetryKey(
        "bmp280.altitude",
        {"sensor": "bmp280", "name": "Altitude", "unit": "ft"}
    )

    # Accelerometer
    ACCEL_X = TelemetryKey(
        "accel.x",
        {"sensor": "accel", "name": "X", "unit": "g"}
    )
    ACCEL_Y = TelemetryKey(
        "accel.y",
        {"sensor": "accel", "name": "Y", "unit": "g"}
    )
    ACCEL_Z = TelemetryKey(
        "accel.z",
        {"sensor": "accel", "name": "Z", "unit": "g"}
    )
    GYRO_X = TelemetryKey(
        "gyro.x",
        {"sensor": "gyro", "name": "X", "unit": "deg/s"}
    )
    GYRO_Y = TelemetryKey(
        "gyro.y",
        {"sensor": "gyro", "name": "Y", "unit": "deg/s"}
    )
    GYRO_Z = TelemetryKey(
        "gyro.z",
        {"sensor": "gyro", "name": "Z", "unit": "deg/s"}
    )
    # ACCEL_TEMP      = TelemetryKey("accel.temperature", "Temperature", "C")
    ACCEL_TEMP      = TelemetryKey(
        "accel.temperature",
        {"sensor": "accel", "name": "Temperature", "unit": "C"}
    )

    # Magnetometer
    MAG_X = TelemetryKey(
        "mag.x",
        {"sensor": "mag", "name": "X", "unit": "uT"}
    )
    MAG_Y = TelemetryKey(
        "mag.y",
        {"sensor": "mag", "name": "Y", "unit": "uT"}
    )
    MAG_Z = TelemetryKey(
        "mag.z",
        {"sensor": "mag", "name": "Z", "unit": "uT"}
    )

    # Temp Sensor
    TEMP_SENSOR     = TelemetryKey(
        "temp.temperature",
        {"sensor": "temp", "name": "Temperature", "unit": "C"}
    )

    # GPS
    GPS_LATITUDE = TelemetryKey(
        "gps.latitude", 
        {"sensor": "gps", "name": "Latitude", "unit": "degrees"}
    )
    GPS_LONGITUDE = TelemetryKey(
        "gps.longitude", 
        {"sensor": "gps", "name": "Longitude", "unit": "degrees"}
    )
    GPS_ALTITUDE = TelemetryKey(
        "gps.altitude", 
        {"sensor": "gps", "name": "Altitude", "unit": "m"}
    )
    GPS_SPEED = TelemetryKey(
        "gps.speed", 
        {"sensor": "gps", "name": "Speed", "unit": "m/s"}
    )
    GPS_ANGLE = TelemetryKey(
        "gps.angle", 
        {"sensor": "gps", "name": "Angle", "unit": "degrees"}
    )

    # Timestamp
    TIMESTAMP = TelemetryKey(
        "timestamp",
        {"sensor": "system", "name": "Timestamp", "unit": "ms"}
    )

    # All keys
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
        GPS_ANGLE,
        TIMESTAMP
    ]

class RedisHelper():
    def __init__(self, host='localhost', port=6379, db=0, flight_name="LC2025"):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.redis_ts = self.redis.ts()
        self.flight_name = flight_name
        if self.redis.ping():
            print("Connected to Redis")
            for k in TelemetryKeys.KEYS:
                key = f"{flight_name}.{k.key}" # Prefix keys with flight name
                if not self.redis.exists(key):
                    self.redis_ts.create(key,
                                         retention_msecs=604800000,
                                         labels=k.labels
                                        )  # 7 days retention
                    print(f"Created timeseries for {key}")
            self.redis.set("current_flight", flight_name)
        else:
            print("Failed to connect to Redis")
    
    def _key(self, key: Tuple[TelemetryKey, str]) -> str:
        """
        Helper function to format the key with flight name.
        """
        return f"{self.flight_name}.{str(key)}"

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