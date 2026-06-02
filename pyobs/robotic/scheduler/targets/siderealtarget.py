from typing import Self
from astropy.coordinates import SkyCoord
from pydantic import model_validator, PrivateAttr

from pyobs.utils.time import Time
from .target import Target


class SiderealTarget(Target):
    ra: float
    dec: float

    _coord: SkyCoord = PrivateAttr(default=SkyCoord(0.0, 0.0, unit="deg"))

    @model_validator(mode="after")
    def cache_coordinates(self) -> Self:
        self._coord = SkyCoord(ra=self.ra, dec=self.dec, frame="icrs", unit="deg")
        return self

    @property
    def coord(self) -> SkyCoord:
        return self._coord

    def coordinates(self, time: Time) -> SkyCoord:
        return self._coord

    def __str__(self) -> str:
        return f"{self.name} ({self._coord})"


__all__ = ["SiderealTarget"]
