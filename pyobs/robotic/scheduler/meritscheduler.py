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
from pyobs.robotic import ScheduledTask

if TYPE_CHECKING:
    from pyobs.robotic import Task

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

        # find current best task
        task, merit = find_next_best_task(tasks, start, data)

        if task is not None and merit is not None:
            # check, whether there is another task within its duration that  will have a higher merit
            better_task, better_time = check_for_better_task(task, merit, tasks, start, data)

            # if better_task is not None and better_time is not None:

            yield create_scheduled_task(task, start)

    async def abort(self) -> None:
        self._abort.set()


def create_scheduled_task(task: Task, time: Time) -> ScheduledTask:
    return ScheduledTask(task, time, time + TimeDelta(task.duration * u.second))


def evaluate_merits(tasks: list[Task], time: Time, data: DataProvider) -> list[float]:
    # evaluate all merit functions at given time
    merits: list[float] = []
    for task in tasks:
        merit = float(np.prod([m(time, task, data) for m in task.merits]))
        merits.append(merit)
    return merits


def find_next_best_task(tasks: list[Task], time: Time, data: DataProvider) -> tuple[Task, float]:
    # evaluate all merit functions at given time
    merits = evaluate_merits(tasks, time, data)

    # find max one
    idx = np.argmax(merits)
    task = tasks[idx]
    return task, merits[idx]


def check_for_better_task(
    task: Task, merit: float, tasks: list[Task], time: Time, data: DataProvider, step: float = 300
) -> tuple[Task | None, Time | None]:
    t = time + TimeDelta(step * u.second)
    while t < time + TimeDelta(task.duration * u.second):
        merits = evaluate_merits(tasks, t, data)
        for i, m in enumerate(merits):
            if m > merit:
                return tasks[i], t
        t += TimeDelta(step * u.second)
    return None, None


__all__ = ["MeritScheduler"]
