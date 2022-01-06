from abc import ABCMeta, abstractmethod
from typing import Tuple, Any

from .interface import Interface


class IPointingAltAz(Interface, metaclass=ABCMeta):
    """The module can move to Alt/Az coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            ValueError: If device could not move.
        """
        ...

    @abstractmethod
    async def get_altaz(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        ...


__all__ = ["IPointingAltAz"]
