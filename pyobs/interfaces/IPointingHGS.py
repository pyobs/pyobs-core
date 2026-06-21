from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .interface import Interface


class IPointingHGS(Interface, metaclass=ABCMeta):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def move_hgs_lon_lat(
        self, lon: Annotated[float, Unit.DEGREES], lat: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Moves on given coordinates.

        Args:
            lon: Longitude in deg to track.
            lat: Latitude in deg to track.

        Raises:
            MoveError: If device could not be moved.
        """
        ...

    @abstractmethod
    async def get_hgs_lon_lat(
        self, **kwargs: Any
    ) -> tuple[Annotated[float, Unit.DEGREES], Annotated[float, Unit.DEGREES]]:
        """Returns current longitude and latitude position.

        Returns:
            Tuple of current lon, lat in degrees.
        """
        ...


__all__ = ["IPointingHGS"]
