from .interface import *


class IAcquisition(Interface):
    def acquire_target(self, ra: float, dec: float, *args, **kwargs):
        """Acquire target at given coordinates.

        Args:
            ra: Right ascension of target to acquire.
            dec: Declination of target to acquire.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
