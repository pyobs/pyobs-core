from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from pyobs.utils.serialization import SubClassBaseModel

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class Merit(SubClassBaseModel, metaclass=ABCMeta):
    """Merit class."""

    @abstractmethod
    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...


__all__ = ["Merit"]
