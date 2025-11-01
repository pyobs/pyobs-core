from abc import ABCMeta, abstractmethod
from typing import Any
from astropy.time import Time

from ..dataprovider import DataProvider
from pyobs.robotic import Task


class Merit(metaclass=ABCMeta):
    """Merit class."""

    def __init__(self, data_provider: DataProvider, **kwargs: Any) -> None:
        self._data_provider = data_provider

    @abstractmethod
    def __call__(self, time: Time, task: Task, data: DataProvider) -> float: ...


__all__ = ["Merit"]
