from .interface import *


class IAcquisition(Interface):
    def acquire_target(self, exposure_time: int, *args, **kwargs):
        """Acquire target at given coordinates.

        Args:
            exposure_time: Exposure time for acquisition.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
