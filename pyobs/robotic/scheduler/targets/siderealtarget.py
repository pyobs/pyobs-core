from typing import Any

from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time
from .target import Target


class SiderealTarget(Target):
    def __init__(self, coord: SkyCoord, **kwargs: Any) -> None:
        Target.__init__(self, **kwargs)
        self._coord = coord

    @property
    def coord(self) -> SkyCoord:
        return self._coord

    def coordinates(self, time: Time) -> SkyCoord:
        return self._coord


__all__ = ["SiderealTarget"]
