from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import WeatherSensors

from ..utils.time import Time
from .IStartStop import IStartStop


@dataclass
class WeatherSensorReading:  # WeatherState.readings element
    sensor: WeatherSensors
    value: float
    unit: str
    time: Time = field(default_factory=Time.now)


@dataclass
class WeatherState:
    good: bool
    readings: list[WeatherSensorReading] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


class IWeather(IStartStop, metaclass=ABCMeta):
    """The module acts as a weather station."""

    __module__ = "pyobs.interfaces"

    state = WeatherState

    @abstractmethod
    async def get_sensor_value(self, station: str, sensor: WeatherSensors, **kwargs: Any) -> WeatherSensorReading:
        """Return value for given sensor.

        Args:
            station: Name of weather station to get value from.
            sensor: Name of sensor to get value from.

        Returns:
            Current reading for the given sensor.

        Raises:
            InvalidArgumentError: If station or sensor is unknown.
            WeatherResponseError: If the underlying weather station's response is malformed.
        """
        ...


__all__ = ["IWeather", "WeatherState", "WeatherSensorReading"]
