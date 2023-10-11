from abc import ABCMeta, abstractmethod
from typing import Tuple, Any

from .interface import Interface


class IPointingHelioprojective(Interface, metaclass=ABCMeta):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def move_helioprojective(self, theta_x: float, theta_y: float, **kwargs: Any) -> None:
        """Moves on given coordinates.

        Args:
            theta_x: The theta_x coordinate.
            theta_y: The theta_y coordinate.

        Raises:
            MoveError: If device could not be moved.
        """
        ...

    @abstractmethod
    async def get_helioprojective(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current theta x/y

        Returns:
            Tuple of current theta x/y in degrees.
        """
        ...


__all__ = ["IPointingHelioprojective"]
