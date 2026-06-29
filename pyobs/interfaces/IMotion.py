from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pyobs.utils.enums import MotionStatus

from ..utils.time import Time
from .IReady import IReady


@dataclass
class DeviceMotionStatus:
    name: str
    status: MotionStatus


@dataclass
class MotionState:
    status: MotionStatus
    devices: list[DeviceMotionStatus] = field(default_factory=list)
    time: Time = field(default_factory=Time.now)


class IMotion(IReady, metaclass=ABCMeta):
    """The module controls a device that can move."""

    __module__ = "pyobs.interfaces"

    state = MotionState

    @abstractmethod
    async def init(self, **kwargs: Any) -> None:
        """Initialize device.

        Raises:
            InitError: If device could not be initialized.
        """
        ...

    @abstractmethod
    async def park(self, **kwargs: Any) -> None:
        """Park device.

        Raises:
            ParkError: If device could not be parked.
        """
        ...

    @abstractmethod
    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        ...


__all__ = ["IMotion", "DeviceMotionStatus", "MotionState"]
