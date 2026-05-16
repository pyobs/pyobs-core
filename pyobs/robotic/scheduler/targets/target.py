import abc
from abc import ABCMeta
from astropy.coordinates import SkyCoord

from pyobs.utils.serialization import SubClassBaseModel
from pyobs.utils.time import Time


class Target(SubClassBaseModel, metaclass=ABCMeta):
    name: str

    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
