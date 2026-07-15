from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class HeliocentricPolarState:
    mu: float
    psi: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IPointingHeliocentricPolar(Interface, metaclass=ABCMeta):
    """The module can move to Heliocentric Polar (Mu/Psi) coordinates, usually combined with
    :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    state = HeliocentricPolarState

    @abstractmethod
    async def move_heliocentric_polar(self, mu: float, psi: Annotated[float, Unit.DEGREES], **kwargs: Any) -> None:
        """Moves on given coordinates.

        Args:
            mu: Cosine of the angular distance from Sun centre, dimensionless (0..1).
            psi: Position angle around the solar disk, in degrees.

        Raises:
            MoveError: If device could not be moved.
        """
        ...


__all__ = ["IPointingHeliocentricPolar", "HeliocentricPolarState"]
