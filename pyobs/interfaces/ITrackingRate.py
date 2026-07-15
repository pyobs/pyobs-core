from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class TrackingRateState:
    ra_rate: Annotated[float, Unit.ARCSEC_PER_SEC]
    dec_rate: Annotated[float, Unit.ARCSEC_PER_SEC]
    time: Time = field(default_factory=Time.now)


@dataclass
class TrackingRateCapabilities:
    min_update_interval: Annotated[float, Unit.SECONDS]
    """Minimum time between successive set_tracking_rate calls this hardware/protocol accepts,
    independent of whether the value actually changed. Populated per-driver from whatever its
    protocol allows; 0 if the hardware has no such floor."""


class ITrackingRate(Interface, metaclass=ABCMeta):
    """The module accepts an arbitrary non-sidereal tracking rate as an absolute RA/Dec offset."""

    __module__ = "pyobs.interfaces"

    state = TrackingRateState
    capabilities = TrackingRateCapabilities

    @abstractmethod
    async def set_tracking_rate(
        self,
        ra_rate: Annotated[float, Unit.ARCSEC_PER_SEC],
        dec_rate: Annotated[float, Unit.ARCSEC_PER_SEC],
        **kwargs: Any,
    ) -> None:
        """Sets an absolute tracking rate on the sky, in arcsec/sec.

        Args:
            ra_rate: Rate in RA, arcsec/sec on the sky.
            dec_rate: Rate in Dec, arcsec/sec on the sky.

        Raises:
            MoveError: If rate could not be set.
        """
        ...


__all__ = ["ITrackingRate", "TrackingRateState", "TrackingRateCapabilities"]
