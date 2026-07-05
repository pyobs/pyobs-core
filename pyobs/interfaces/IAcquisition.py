from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
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


class IAcquisition(IRunning, IAbortable, metaclass=ABCMeta):
    """The module can acquire a target, usually by accessing a telescope and a camera."""

    __module__ = "pyobs.interfaces"

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


__all__ = ["AcquisitionResult", "IAcquisition"]
