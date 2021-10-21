from typing import Tuple, Any

from .interface import Interface
from pyobs.utils.enums import WeatherSensors


class IWeather(Interface):
    """The module acts as a weather station."""
    __module__ = 'pyobs.interfaces'

    def get_weather_status(self, **kwargs: Any) -> dict:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        raise NotImplementedError

    def is_weather_good(self, **kwargs: Any) -> bool:
        """Whether the weather is good to observe."""
        raise NotImplementedError

    def get_current_weather(self, **kwargs: Any) -> dict:
        """Returns current weather.

        Returns:
            Dictionary containing entries for time, good, and sensor, with the latter being another dictionary
            with sensor information, which contain a value and a good flag.
        """
        raise NotImplementedError

    def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> Tuple[str, float]:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """
        raise NotImplementedError


__all__ = ['IWeather']
