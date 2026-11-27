from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from pydantic import Field

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class RandomMerit(Merit):
    """Random factor drawn from a normal distribution with mean 1, clipped at 0.

    Merits are multiplied, so a mean of 1 adds noise around the other merits (e.g. to break ties)
    without shifting them on average.
    """

    std: float = Field(ge=0.0, le=1.0, default=0.1)

    def max_value(self) -> float:
        # a normal distribution is unbounded
        return 1.0 if self.std == 0 else math.inf

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return max(0.0, float(np.random.normal(1.0, self.std)))


__all__ = ["RandomMerit"]
