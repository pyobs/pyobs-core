from abc import ABCMeta
from typing import Tuple, Any, Dict

from .IAbortable import IAbortable


class IAutoFocus(IAbortable, metaclass=ABCMeta):
    """The module can perform an auto-focus."""
    __module__ = 'pyobs.interfaces'

    async def auto_focus(self, count: int, step: float, exposure_time: float, **kwargs: Any) \
            -> Tuple[float, float]:
        """Perform an auto-focus series.

        This method performs an auto-focus series with "count" images on each side of the initial guess and the given
        step size. With count=3, step=1 and guess=10, this takes images at the following focus values:
        7, 8, 9, 10, 11, 12, 13

        Args:
            count: Number of images to take on each side of the initial guess. Should be an odd number.
            step: Step size.
            exposure_time: Exposure time for images.

        Returns:
            Tuple of obtained best focus value and its uncertainty.

        Raises:
            ValueError: If focus could not be obtained.
        """
        raise NotImplementedError

    async def auto_focus_status(self, **kwargs: Any) -> Dict[str, Any]:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        raise NotImplementedError


__all__ = ['IAutoFocus']
