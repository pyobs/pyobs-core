from __future__ import annotations
from typing import Any, TYPE_CHECKING
import numpy as np
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class RandomMerit(Merit):
    """Merit functions for a random normal-distributed number."""

    def __init__(self, std: float = 1.0, **kwargs: Any):
        super().__init__(**kwargs)
        self._std = std

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return np.random.normal(0.0, self._std)


__all__ = ["RandomMerit"]
