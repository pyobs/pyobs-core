from enum import Enum

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


__all__ = ['IWeather']
