from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class HGSState:
    lon: Annotated[float, Unit.DEGREES]
    lat: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IPointingHGS(Interface, metaclass=ABCMeta):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    state = HGSState

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


__all__ = ["IPointingHGS", "HGSState"]
