from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


class IOffsetsRaDec(Interface, metaclass=ABCMeta):
    """The module supports RA/Dec offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IPointingRaDec`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        ra: Annotated[float, Unit.DEGREES]
        dec: Annotated[float, Unit.DEGREES]
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_offsets_radec(
        self, dra: Annotated[float, Unit.DEGREES], ddec: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Move an RA/Dec offset.

        Args:
            dra: RA offset in degrees.
            ddec: Dec offset in degrees.

        Raises:
            MoveError: If telescope cannot be moved.
        """
        ...

    @abstractmethod
    async def get_offsets_radec(self, **kwargs: Any) -> IOffsetsRaDec.State:
        """Get RA/Dec offset.

        Returns:
            Tuple with RA and Dec offsets.
        """
        ...


__all__ = ["IOffsetsRaDec"]
