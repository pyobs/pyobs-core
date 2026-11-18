from __future__ import annotations

from datetime import time as dtime
from typing import TYPE_CHECKING

from pydantic import Field

from pyobs.utils.time import Time

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class TimeOfDayMerit(Merit):
    """Merit function that is only non-zero within a daily time window (UTC).

    The window is half-open, [start, end). If start > end, the window wraps around midnight.
    """

    start: dtime = Field(default=dtime(0, 0))
    end: dtime = Field(default=dtime(0, 0))
    inverse: bool = False

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # time of day in UTC
        now = time.utc.datetime.time()

        # in window? start == end means an empty window
        if self.start <= self.end:
            in_window = self.start <= now < self.end
        else:
            in_window = now >= self.start or now < self.end

        # invert?
        if not self.inverse:
            return 1.0 if in_window else 0.0
        else:
            return 0.0 if in_window else 1.0


__all__ = ["TimeOfDayMerit"]
