import abc
from abc import ABCMeta
from astropy.coordinates import SkyCoord

from pyobs.robotic.utils.serialization import PolymorphicBaseModel
from pyobs.utils.time import Time


class Target(PolymorphicBaseModel, metaclass=ABCMeta):
    name: str

    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
