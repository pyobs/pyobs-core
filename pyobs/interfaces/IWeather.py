from abc import ABCMeta, abstractmethod
from typing import Tuple, Any, Dict

from .IStartStop import IStartStop
from pyobs.utils.enums import WeatherSensors


class IWeather(IStartStop, metaclass=ABCMeta):
    """The module acts as a weather station."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def get_weather_status(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns status of object in form of a dictionary. See other interfaces for details."""
        ...

    @abstractmethod
    async def is_weather_good(self, **kwargs: Any) -> bool:
        """Whether the weather is good to observe."""
        ...

    @abstractmethod
    async def get_current_weather(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns current weather.

        Returns:
            Dictionary containing entries for time, good, and sensor, with the latter being another dictionary
            with sensor information, which contain a value and a good flag.
        """
        ...

    @abstractmethod
    async def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> Tuple[str, float]:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Tuple of current value of given sensor or None and time of measurement or None.
        """
        ...


__all__ = ['IWeather']
