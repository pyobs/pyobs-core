from typing import Tuple

from .IAbortable import IAbortable


class IFlatField(IAbortable):
    def flat_field(self, filter_name: str, count: int = 20, binning: int = 1, *args, **kwargs) -> Tuple[int, float]:
        """Do a series of flat fields in the given filter.

        Args:
            filter_name: Name of filter
            count: Number of images to take
            binning: Binning to use

        Returns:
            Number of images actually taken and total exposure time in ms
        """
        raise NotImplementedError

    def flat_field_status(self, *args, **kwargs) -> dict:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status
        """
        raise NotImplementedError


__all__ = ['IFlatField']
