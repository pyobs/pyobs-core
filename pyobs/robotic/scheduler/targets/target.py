from __future__ import annotations
import abc
from abc import ABCMeta
from astropy.coordinates import SkyCoord
from typing import TYPE_CHECKING

from pyobs.utils.serialization import PolymorphicBaseModel
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.robotic.scheduler import DataProvider


class Target(PolymorphicBaseModel, metaclass=ABCMeta):
    name: str

    async def resolve(self, time: Time, task: Task, data: DataProvider) -> Target | None:
        """For dynamic targets. Pick the best available target given current conditions."""
        return self

    @abc.abstractmethod
    def coordinates(self, time: Time) -> SkyCoord: ...


__all__ = ["Target"]
