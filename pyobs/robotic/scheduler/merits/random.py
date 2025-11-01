from typing import Any
from astropy.time import Time
import numpy as np

from pyobs.robotic import Task
from .merit import Merit
from ..dataprovider import DataProvider


class RandomMerit(Merit):
    """Merit functions for a random normal-distributed number."""

    def __init__(self, std: float = 1.0, **kwargs: Any):
        super().__init__(**kwargs)
        self._std = std

    def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return np.random.normal(0.0, self._std)


__all__ = ["RandomMerit"]
