from abc import ABCMeta, abstractmethod
from typing import Tuple, Any

from .interface import Interface


class ILatLon(Interface, metaclass=ABCMeta):
    """The module can move to general Lat/Lon coordinates, which have to be async defined by the module itself.
    Usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def move_latlon(self, lat: float, lon: float, **kwargs: Any) -> None:
        """Moves to given coordinates.

        Args:
            lat: Latitude in deg to move to.
            lon: Longitude in deg to move to.

        Raises:
            ValueError: If device could not move.
        """
        ...

    @abstractmethod
    async def get_latlon(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current Latitude and Longitude.

        Returns:
            Tuple of current Latitude and Longitude in degrees.
        """
        ...


__all__ = ["ILatLon"]
