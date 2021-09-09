from typing import Tuple

from .IAbortable import IAbortable


class IFlatField(IAbortable):
    """The module performs flat-fielding."""
    __module__ = 'pyobs.interfaces'

    def flat_field(self, count: int = 20, *args, **kwargs) -> Tuple[int, float]:
        """Do a series of flat fields.

        Args:
            count: Number of images to take

        Returns:
            Number of images actually taken and total exposure time in ms
        """
        raise NotImplementedError


__all__ = ['IFlatField']
