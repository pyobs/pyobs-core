from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .interface import Interface


class IPointingRaDec(Interface, metaclass=ABCMeta):
    """The module can move to RA/Dec coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def move_radec(
        self, ra: Annotated[float, Unit.DEGREES], dec: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            MoveError: If device could not be moved.
        """
        ...

    @abstractmethod
    async def get_radec(self, **kwargs: Any) -> tuple[Annotated[float, Unit.DEGREES], Annotated[float, Unit.DEGREES]]:
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        ...


__all__ = ["IPointingRaDec"]
