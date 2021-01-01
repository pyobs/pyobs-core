from enum import Enum
from typing import Union, Tuple

from .interface import Interface


class IWeather(Interface):
    class Sensors(Enum):
        TIME = 'time'               # in iso format
        TEMPERATURE = 'temp'        # in °C
        HUMIDITY = 'humid'          # in %
        PRESSURE = 'press'          # in hPa
        WINDDIR = 'winddir'         # in degrees azimuth
        WINDSPEED = 'windspeed'     # in km/h
        RAIN = 'rain'               # 0/1
        SKYTEMP = 'skytemp'         # in °C
        DEWPOINT = 'dewpoint'       # in °C
        PARTICLES = 'particles'     # in particles per m³

    def get_weather_status(self, *args, **kwargs) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError

    def is_weather_good(self, *args, **kwargs) -> bool:
        """Whether the weather is good to observe."""
        raise NotImplementedError

    def get_current_weather(self, *args, **kwargs) -> dict:
        """Returns current weather.

        Returns:
            Dictionary containing entries for time, good, and sensor, with the latter being another dictionary
            with sensor information, which contain a value and a good flag.
        """
        raise NotImplementedError

    def get_sensor_value(self, station: str, sensor: Sensors, *args, **kwargs) -> Tuple[str, float]:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """
        raise NotImplementedError


__all__ = ['IWeather']
