from abc import ABCMeta, abstractmethod
from typing import Any

from .IMotion import IMotion


class IRotation(IMotion, metaclass=ABCMeta):
    """The module controls a device that can rotate."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def set_rotation(self, angle: float, **kwargs: Any) -> None:
        """Sets the rotation angle to the given value in degrees."""
        ...

    @abstractmethod
    async def get_rotation(self) -> float:
        """Returns the current rotation angle."""
        ...

    @abstractmethod
    async def track(self, ra: float, dec: float, **kwargs: Any) -> None:
        """Tracks the position angle of a rotator for an alt-az telescope."""
        ...


__all__ = ["IRotation"]
