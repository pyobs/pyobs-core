from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Annotated

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class SensorReading:
    name: str
    value: Annotated[float, Unit.CELSIUS]


@dataclass
class TemperaturesState:
    readings: list[SensorReading] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""

    __module__ = "pyobs.interfaces"

    state = TemperaturesState


__all__ = ["ITemperatures", "SensorReading", "TemperaturesState"]
