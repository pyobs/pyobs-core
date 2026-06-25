from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Annotated

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface

# --- ITemperatures / IWeather support ---


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class Temperature:
        name: str
        value: Annotated[float, Unit.CELSIUS]

    @dataclass
    class State:
        readings: list[ITemperatures.Temperature] = field(default_factory=list)
        time: Time = field(default_factory=Time.now)


__all__ = ["ITemperatures"]
