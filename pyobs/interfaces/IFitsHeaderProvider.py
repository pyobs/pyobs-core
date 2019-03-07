from .interface import *


class IFitsHeaderProvider(Interface):
    def get_fits_headers(self, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """
        raise NotImplementedError


__all__ = ['IFitsHeaderProvider']
