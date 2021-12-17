from abc import ABCMeta
from typing import Tuple, Any

from .IAbortable import IAbortable


class IFlatField(IAbortable, metaclass=ABCMeta):
    """The module performs flat-fielding."""
    __module__ = 'pyobs.interfaces'

    async def flat_field(self, count: int = 20, **kwargs: Any) -> Tuple[int, float]:
        """Do a series of flat fields.

        Args:
            count: Number of images to take

        Returns:
            Number of images actually taken and total exposure time in ms
        """
        raise NotImplementedError


__all__ = ['IFlatField']
