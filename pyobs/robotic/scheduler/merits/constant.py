from typing import Any
from astropy.time import Time

from pyobs.robotic import Task
from .merit import Merit
from ..dataprovider import DataProvider


class ConstantMerit(Merit):
    """Merit function that returns a constant value."""

    def __init__(self, merit: float, **kwargs: Any):
        super().__init__(**kwargs)
        self._merit = merit

    def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return self._merit


__all__ = ["ConstantMerit"]
