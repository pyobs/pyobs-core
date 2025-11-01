from __future__ import annotations
from functools import cache
from typing import TYPE_CHECKING
from .avoidance import AvoidanceMerit

if TYPE_CHECKING:
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from .. import DataProvider


class MoonAvoidanceMerit(AvoidanceMerit):
    """Merit functions that works on the distance to the moon."""

    @cache
    def _avoidance_position(self, time: Time, data: DataProvider) -> SkyCoord:
        return data.get_moon(time)


__all__ = ["MoonAvoidanceMerit"]
