import abc
from abc import ABCMeta
from astropy.coordinates import SkyCoord

from pyobs.utils.serialization import PolymorphicBaseModel
from pyobs.utils.time import Time


class Target(PolymorphicBaseModel, metaclass=ABCMeta):
    name: str

    async def resolve(self, time: Time) -> None:
        """For dynamic targets. Pick the best available target given current conditions."""
        ...

    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
