from __future__ import annotations
import asyncio
import logging
from typing import Any, TYPE_CHECKING
from collections.abc import AsyncIterator
import numpy as np
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.object import Object
from . import DataProvider
from .taskscheduler import TaskScheduler
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import ScheduledTask, Task

log = logging.getLogger(__name__)


class MeritScheduler(TaskScheduler):
    """Scheduler based on merits."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        schedule_range: int = 24,
        safety_time: float = 60,
        twilight: str = "astronomical",
        **kwargs: Any,
    ):
        """Initialize a new scheduler.

        Args:
            schedule_range: Number of hours to schedule into the future
            safety_time: If no ETA for next task to start exists (from current task, weather became good, etc), use
                         this time in seconds to make sure that we don't schedule for a time when the scheduler is
                         still running
            twilight: astronomical or nautical
        """
        Object.__init__(self, **kwargs)

        # store
        self._schedule_range = schedule_range
        self._safety_time = safety_time
        self._twilight = twilight
        self._abort: asyncio.Event = asyncio.Event()

    async def schedule(self, tasks: list[Task], start: Time) -> AsyncIterator[ScheduledTask]:
        data = DataProvider(self.observer)
        task = await self._find_next_best_task(tasks, start, data)
        yield task

    async def _find_next_best_task(self, tasks: list[Task], time: Time, data: DataProvider) -> ScheduledTask:
        # evaluate all merit functions at given time
        merits: list[float] = []
        for task in tasks:
            merit = float(np.prod([m(time, task, data) for m in task.merits]))
            merits.append(merit)

        # find max one
        idx = np.argmax(merits)
        task = tasks[idx]
        return ScheduledTask(task, time, time + TimeDelta(task.duration * u.sec))

    async def abort(self) -> None:
        self._abort.set()


__all__ = ["MeritScheduler"]
