from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .interface import Interface


class IOffsetsRaDec(Interface, metaclass=ABCMeta):
    """The module supports RA/Dec offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IPointingRaDec`."""

    __module__ = "pyobs.interfaces"

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
    async def get_offsets_radec(
        self, **kwargs: Any
    ) -> tuple[Annotated[float, Unit.DEGREES], Annotated[float, Unit.DEGREES]]:
        """Get RA/Dec offset.

        Returns:
            Tuple with RA and Dec offsets.
        """
        ...


__all__ = ["IOffsetsRaDec"]
