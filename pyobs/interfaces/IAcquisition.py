from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IAbortable import IAbortable
from .IRunning import IRunning


class OffsetFrame(StrEnum):
    """Coordinate frame an acquisition offset is expressed in, whichever the mount supports."""

    RA_DEC = "radec"
    ALT_AZ = "altaz"


@dataclass
class AcquisitionResult:
    time: Time
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    offset_frame: OffsetFrame | None = None
    # (ra, dec) if offset_frame is RA_DEC, (alt, az) if ALT_AZ
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None


@dataclass
class AcquisitionAttempt:  # AcquisitionState.attempts element
    attempt: int
    distance: Annotated[float, Unit.ARCSEC]
    offset_applied: bool
    # accumulated telescope offset after this attempt; (ra, dec) if offset_frame is RA_DEC, (alt, az) if ALT_AZ
    offset_frame: OffsetFrame | None = None
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None


@dataclass
class AcquisitionState:  # growing log of attempts during an acquisition run
    attempts: list[AcquisitionAttempt] = field(default_factory=list)
    result: AcquisitionResult | None = None
    time: Time = field(default_factory=Time.now)


class IAcquisition(IRunning, IAbortable, metaclass=ABCMeta):
    """The module can acquire a target, usually by accessing a telescope and a camera."""

    __module__ = "pyobs.interfaces"

    state = AcquisitionState

    @abstractmethod
    async def acquire_target(self, **kwargs: Any) -> AcquisitionResult:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Returns:
            Result with time, ra, dec, alt, az, and an offset in whichever frame the mount supports.

        Raises:
            ValueError: If target could not be acquired.
        """
        ...


__all__ = ["AcquisitionResult", "AcquisitionAttempt", "AcquisitionState", "OffsetFrame", "IAcquisition"]
