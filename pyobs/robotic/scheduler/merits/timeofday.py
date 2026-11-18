from __future__ import annotations

from datetime import time as dtime
from typing import TYPE_CHECKING

from pydantic import Field

from pyobs.utils.serialization import BaseModel
from pyobs.utils.time import Time

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class TimeOfDayWindow(BaseModel):
    """Daily window [start, end) in UTC. If start > end, the window wraps around midnight."""

    start: dtime = Field(default=dtime(0, 0))
    end: dtime = Field(default=dtime(0, 0))

    def contains(self, now: dtime) -> bool:
        # start == end means an empty window
        if self.start <= self.end:
            return self.start <= now < self.end
        return now >= self.start or now < self.end


class TimeOfDayMerit(Merit):
    """Merit function that is only non-zero within daily time windows (UTC).

    Multiple windows are ORed. Several merits are ANDed by the scheduler, so use one merit with several windows."""

    windows: list[TimeOfDayWindow] = Field(default_factory=list)
    inverse: bool = False

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # time of day in UTC
        now = time.utc.datetime.time()

        # in any window?
        in_window = any(window.contains(now) for window in self.windows)

        # invert?
        if not self.inverse:
            return 1.0 if in_window else 0.0
        else:
            return 0.0 if in_window else 1.0


__all__ = ["TimeOfDayMerit", "TimeOfDayWindow"]
