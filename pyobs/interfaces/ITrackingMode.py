from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..utils.time import Time
from .interface import Interface


class TrackingMode(StrEnum):
    """Discrete, hardware-native tracking rate."""

    SIDEREAL = "sidereal"
    SOLAR = "solar"
    LUNAR = "lunar"
    OFF = "off"


@dataclass
class TrackingModeState:
    mode: TrackingMode
    time: Time = field(default_factory=Time.now)


@dataclass
class TrackingModeCapabilities:
    modes: list[TrackingMode]


class ITrackingMode(Interface, metaclass=ABCMeta):
    """The module supports switching between discrete, hardware-native tracking rates."""

    __module__ = "pyobs.interfaces"

    state = TrackingModeState
    capabilities = TrackingModeCapabilities

    @abstractmethod
    async def set_tracking_mode(self, mode: TrackingMode, **kwargs: Any) -> None:
        """Switches to the given tracking mode.

        Args:
            mode: Tracking mode to switch to.

        Raises:
            MoveError: If mode could not be set.
            ValueError: If mode is not in this module's capabilities.
        """
        ...


__all__ = ["ITrackingMode", "TrackingMode", "TrackingModeState", "TrackingModeCapabilities"]
