from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time
from .target import Target


class SiderealTarget(Target):
    def __init__(self, name: str, coord: SkyCoord):
        super().__init__()
        self._name = name
        self._coord = coord

    @property
    def name(self) -> str:
        return self._name

    @property
    def coord(self) -> SkyCoord:
        return self._coord

    def coordinates(self, time: Time) -> SkyCoord:
        return self._coord


__all__ = ["SiderealTarget"]
