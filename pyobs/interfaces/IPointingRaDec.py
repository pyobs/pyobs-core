from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class RaDecState:
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IPointingRaDec(Interface, metaclass=ABCMeta):
    """The module can move to RA/Dec coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    state = RaDecState

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


__all__ = ["IPointingRaDec", "RaDecState"]
