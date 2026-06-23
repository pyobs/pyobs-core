from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


# --- ITemperatures / IWeather support ---
@dataclass
class Temperature:
    name: str
    value: Annotated[float, Unit.CELSIUS]


@dataclass
class TemperaturesState:
    readings: list[Temperature] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""

    __module__ = "pyobs.interfaces"
    state = TemperaturesState

    @abstractmethod
    async def get_temperatures(self, **kwargs: Any) -> TemperaturesState:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        ...


__all__ = ["ITemperatures"]
