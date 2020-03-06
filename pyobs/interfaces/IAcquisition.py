from .interface import *


class IAcquisition(Interface):
    def acquire_target(self, exposure_time: int, ra: float = None, dec: float = None, *args, **kwargs):
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition.
            ra: Right ascension of field to acquire.
            dec: Declination of field to acquire.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
