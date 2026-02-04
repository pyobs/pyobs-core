from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class RandomMerit(Merit):
    """Merit functions for a random normal-distributed number."""

    std: float = 1.0

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return np.random.normal(0.0, self.std)


__all__ = ["RandomMerit"]
