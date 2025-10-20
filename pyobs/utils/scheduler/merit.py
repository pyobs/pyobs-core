from abc import ABCMeta, abstractmethod
from astropy.time import Time

from .dataprovider import DataProvider
from ...robotic import Task


class Merit(metaclass=ABCMeta):
    """Merit class."""

    @abstractmethod
    def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...


__all__ = ["Merit"]
