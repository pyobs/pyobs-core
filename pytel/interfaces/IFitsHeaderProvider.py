from .interface import *


class IFitsHeaderProvider(Interface):
    def get_fits_headers(self, *args, **kwargs) -> dict:
        """get FITS header for the saved status of the telescope"""
        raise NotImplementedError


__all__ = ['IFitsHeaderProvider']
