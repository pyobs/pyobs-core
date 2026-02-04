from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time
from .target import Target


class SiderealTarget(Target):
    ra: float
    dec: float

    @property
    def coord(self) -> SkyCoord:
        return SkyCoord(ra=self.ra, dec=self.dec, frame="icrs", unit="deg")

    def coordinates(self, time: Time) -> SkyCoord:
        return SkyCoord(ra=self.ra, dec=self.dec, frame="icrs", unit="deg")


__all__ = ["SiderealTarget"]
