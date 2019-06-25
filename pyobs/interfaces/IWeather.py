from enum import Enum

from .interface import Interface


class IWeather(Interface):
    class Sensors(Enum):
        TIME = 'time'
        TEMPERATURE = 'temp'
        HUMIDITY = 'humid'
        PRESSURE = 'press'
        WINDDIR = 'winddir'
        WINDSPEED = 'windspeed'
        RAIN = 'rain'
        SKYTEMP = 'skytemp'
        DEWPOINT = 'dewpoint'

    def get_weather_status(self, *args, **kwargs) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError


__all__ = ['IWeather']
