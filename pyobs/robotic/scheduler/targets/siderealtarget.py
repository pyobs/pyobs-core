from typing import Any

from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time
from .target import Target


class SiderealTarget(Target):
    def __init__(self, ra: float, dec: float, **kwargs: Any) -> None:
        Target.__init__(self, **kwargs)
        self._coord = SkyCoord(ra=ra, dec=dec, frame="icrs", unit="deg")

    @property
    def coord(self) -> SkyCoord:
        return self._coord

    def coordinates(self, time: Time) -> SkyCoord:
        return self._coord


__all__ = ["SiderealTarget"]
