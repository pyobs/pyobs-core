from .interface import *


class IAcquisition(Interface):
    def acquire_target(self, ra: float, dec: float, exposure_time: int, *args, **kwargs):
        """Acquire target at given coordinates.

        Args:
            ra: Right ascension of field to acquire.
            dec: Declination of field to acquire.
            exposure_time: Exposure time for acquisition.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
