from enum import Enum

from .IStatus import IStatus


class IWeather(IStatus):
    class Sensors(Enum):
        TEMPERATURE = 'temp'
        HUMIDITY = 'humid'
        PRESSURE = 'press'
        WINDDIR = 'winddir'
        WINDSPEED = 'windspeed'
        RAIN = 'rain'
        SKYTEMP = 'skytemp'
        DEWPOINT = 'dewpoint'

    def status(self, *args, **kwargs) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError


__all__ = ['IWeather']
