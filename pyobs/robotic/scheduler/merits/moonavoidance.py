from functools import cache
from astropy.coordinates import SkyCoord
from astropy.time import Time

from .avoidance import AvoidanceMerit


class MoonAvoidanceMerit(AvoidanceMerit):
    """Merit functions that works on the distance to the moon."""

    @cache
    def _avoidance_position(self, time: Time) -> SkyCoord:
        return self._data_provider.get_moon(time)


__all__ = ["MoonAvoidanceMerit"]
