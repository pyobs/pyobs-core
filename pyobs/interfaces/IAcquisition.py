from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IAbortable import IAbortable
from .IRunning import IRunning


@dataclass
class AcquisitionResult:
    time: Time
    ra: Annotated[float, Unit.DEGREES]
    dec: Annotated[float, Unit.DEGREES]
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    off_ra: Annotated[float, Unit.DEGREES] | None = None
    off_dec: Annotated[float, Unit.DEGREES] | None = None
    off_alt: Annotated[float, Unit.DEGREES] | None = None
    off_az: Annotated[float, Unit.DEGREES] | None = None


@dataclass
class AcquisitionAttempt:  # AcquisitionState.attempts element
    attempt: int
    distance: Annotated[float, Unit.ARCSEC]
    offset_applied: bool
    # accumulated telescope offset after this attempt, whichever pair the mount supports
    offset_ra: Annotated[float, Unit.DEGREES] | None = None
    offset_dec: Annotated[float, Unit.DEGREES] | None = None
    offset_alt: Annotated[float, Unit.DEGREES] | None = None
    offset_az: Annotated[float, Unit.DEGREES] | None = None


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
            Result with time, ra, dec, alt, az, and either off_ra/off_dec or off_alt/off_az offsets.

        Raises:
            ValueError: If target could not be acquired.
        """
        ...


__all__ = ["AcquisitionResult", "AcquisitionAttempt", "AcquisitionState", "IAcquisition"]
