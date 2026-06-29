from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class AltAzOffsetState:
    alt: Annotated[float, Unit.DEGREES]
    az: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IOffsetsAltAz(Interface, metaclass=ABCMeta):
    """The module supports Alt/Az offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IPointingAltAz`."""

    __module__ = "pyobs.interfaces"

    state = AltAzOffsetState

    @abstractmethod
    async def set_offsets_altaz(
        self, dalt: Annotated[float, Unit.DEGREES], daz: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Move an Alt/Az offset.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            MoveError: If device could not be moved.
        """
        ...


__all__ = ["IOffsetsAltAz", "AltAzOffsetState"]
