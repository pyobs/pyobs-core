from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


class IPointingAltAz(Interface, metaclass=ABCMeta):
    """The module can move to Alt/Az coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        alt: Annotated[float, Unit.DEGREES]
        az: Annotated[float, Unit.DEGREES]
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def move_altaz(
        self, alt: Annotated[float, Unit.DEGREES], az: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            MoveError: If device could not be moved.
        """
        ...

    @abstractmethod
    async def get_altaz(self, **kwargs: Any) -> IPointingAltAz.State:
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        ...


__all__ = ["IPointingAltAz"]
