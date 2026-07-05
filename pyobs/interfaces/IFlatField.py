from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .IAbortable import IAbortable


class IFlatField(IAbortable, metaclass=ABCMeta):
    """The module performs flat-fielding."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def flat_field(self, count: int = 20, **kwargs: Any) -> tuple[int, Annotated[float, Unit.SECONDS]]:
        """Do a series of flat fields.

        Args:
            count: Number of images to take

        Returns:
            Number of images actually taken and total exposure time in seconds
        """
        ...


__all__ = ["IFlatField"]
