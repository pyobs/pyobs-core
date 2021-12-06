from typing import Any

from .IMotion import IMotion


class IRotation(IMotion):
    """The module controls a device that can rotate."""
    __module__ = 'pyobs.interfaces'

    async def set_rotation(self, angle: float, **kwargs: Any) -> None:
        """ Sets the rotation angle to the given value in degrees. """
        raise NotImplementedError

    async def get_rotation(self) -> float:
        """ Returns the current rotation angle. """
        raise NotImplementedError

    async def track(self, ra: float, dec: float, **kwargs: Any) -> None:
        """ Tracks the position angle of a rotator for an alt-az telescope. """
        raise NotImplementedError


__all__ = ['IRotation']
