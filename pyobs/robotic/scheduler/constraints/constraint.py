from __future__ import annotations
from abc import ABCMeta, abstractmethod
import astroplan
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class Constraint(metaclass=ABCMeta):
    @abstractmethod
    def to_astroplan(self) -> astroplan.Constraint: ...

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool: ...
