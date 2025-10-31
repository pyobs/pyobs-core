import abc
from abc import ABCMeta

from astropy.coordinates import SkyCoord

from pyobs.object import Object
from pyobs.utils.time import Time


class Target(Object, metaclass=ABCMeta):
    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
