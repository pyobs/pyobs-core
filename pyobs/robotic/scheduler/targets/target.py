import abc
from abc import ABCMeta
from typing import Any

from astropy.coordinates import SkyCoord

from pyobs.object import Object
from pyobs.utils.time import Time


class Target(Object, metaclass=ABCMeta):
    def __init__(self, name: str, **kwargs: Any) -> None:
        Object.__init__(self, **kwargs)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
