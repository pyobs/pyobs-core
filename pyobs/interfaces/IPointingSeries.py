from .interface import *


class IPointingSeries(Interface):
    def pointing_series(self, num_alt: int = 8, num_az: int = 24, *args, **kwargs):
        """Reduces all data within a given range of time.

        Args:
            num_alt: Number of altitude points to create on grid.
            num_az: Number of azimuth points to create on grid.
        """
        raise NotImplementedError


__all__ = ['IPointingSeries']
