from .interface import *


class IAcquisition(Interface):
    def acquire_target(self, exposure_time: int, ra: float = None, dec: float = None, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition.
            ra: Right ascension of field to acquire.
            dec: Declination of field to acquire.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError if target could not be acquired.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
