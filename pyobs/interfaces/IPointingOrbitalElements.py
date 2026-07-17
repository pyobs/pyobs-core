from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class OrbitalElements:
    epoch: Time
    semi_major_axis: Annotated[float, Unit.AU]
    eccentricity: float
    inclination: Annotated[float, Unit.DEGREES]
    longitude_ascending_node: Annotated[float, Unit.DEGREES]
    argument_of_periapsis: Annotated[float, Unit.DEGREES]
    mean_anomaly: Annotated[float, Unit.DEGREES] | None = None
    """Mean anomaly at epoch, in degrees. Required for elliptical orbits (eccentricity < 1)."""
    perihelion_time: Time | None = None
    """Time of perihelion passage. Required for near-parabolic/cometary orbits
    (eccentricity close to or at 1), where mean anomaly is not well-defined."""


class IPointingOrbitalElements(Interface, metaclass=ABCMeta):
    """Points at and tracks a body defined by orbital elements (asteroid, comet, NEO)."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def track_orbital_elements(self, elements: OrbitalElements, **kwargs: Any) -> None:
        """Starts tracking a body defined by orbital elements.

        Args:
            elements: Orbital elements of the body to track.

        Raises:
            NotSupportedError: If this device doesn't support orbital-element tracking.
            InvalidOrbitalElementsError: If elements are incomplete or inconsistent (neither
                mean_anomaly nor perihelion_time given).
            MoveError: If telescope could not be moved. Also propagates whatever the underlying
                RA/Dec move raises (e.g. MissingObserverError, AltitudeLimitError), since tracking
                orbital elements is implemented as propagating them and then moving there.
        """
        ...


__all__ = ["IPointingOrbitalElements", "OrbitalElements"]
