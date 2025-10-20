from typing import Any

from astropy.time import Time

from pyobs.robotic import Task
from ..dataprovider import DataProvider
from ..merit import Merit


class ConstantMerit(Merit):
    """Merit function that returns a constant value."""

    def __init__(self, merit: float, **kwargs: Any):
        self._merit = merit

    def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return self._merit


__all__ = ["ConstantMerit"]
