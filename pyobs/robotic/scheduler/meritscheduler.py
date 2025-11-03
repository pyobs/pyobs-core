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
        twilight: str = "astronomical",
        **kwargs: Any,
    ):
        """Initialize a new scheduler.

        Args:
            twilight: astronomical or nautical
        """
        Object.__init__(self, **kwargs)

        # store
        self._twilight = twilight
        self._abort: asyncio.Event = asyncio.Event()

    async def schedule(self, tasks: list[Task], start: Time, end: Time) -> AsyncIterator[ScheduledTask]:
        data = DataProvider(self.observer)

        # schedule from
        async for task in schedule_in_interval(tasks, start, end, data):
            yield task

    async def abort(self) -> None:
        self._abort.set()


async def schedule_in_interval(
    tasks: list[Task], start: Time, end: Time, data: DataProvider, step: float = 300
) -> AsyncIterator[ScheduledTask]:
    time = start
    while time < end:
        latest_end = start

        # schedule first in this interval, could be one or two
        async for scheduled_task in schedule_first_in_interval(tasks, time, end, data):
            # yield it to caller
            yield scheduled_task

            # check end
            if scheduled_task.end > latest_end:
                latest_end = scheduled_task.end

        if latest_end == start:
            # no task found, so we're finished
            return

        # set new time
        time = latest_end


async def schedule_first_in_interval(
    tasks: list[Task], start: Time, end: Time, data: DataProvider, step: float = 300
) -> AsyncIterator[ScheduledTask]:
    # find current best task
    task, merit = find_next_best_task(tasks, start, end, data)

    if task is not None and merit is not None:
        # check, whether there is another task within its duration that  will have a higher merit
        better_task, better_time, better_merit = check_for_better_task(task, merit, tasks, start, end, data, step=step)

        if better_task is not None and better_time is not None and better_merit is not None:
            # can we maybe postpone the better task to run both?
            postpone_time = can_postpone_task(task, better_task, better_merit, start, end, data)
            if postpone_time is not None:
                # yes, we can! schedule both
                yield create_scheduled_task(task, start)
                yield create_scheduled_task(better_task, postpone_time)
            else:
                # just schedule better_task
                yield create_scheduled_task(better_task, better_time)

                # and find other tasks for in between, new end time is better_time
                async for between_task in schedule_in_interval(tasks, start, better_time, data):
                    yield between_task

        else:
            # this seems to be the best task for now, schedule it
            yield create_scheduled_task(task, start)


def create_scheduled_task(task: Task, time: Time) -> ScheduledTask:
    return ScheduledTask(task, time, time + TimeDelta(task.duration))


def evaluate_merits(tasks: list[Task], start: Time, end: Time, data: DataProvider) -> list[float]:
    # evaluate all merit functions at given time
    merits: list[float] = []
    for task in tasks:
        # if task is too long for the given slot, we evaluate its merits to zero
        if start + TimeDelta(task.duration) > end:
            merit = 0.0
        else:
            # if no merits are present, we evaluate it to 1
            if len(task.merits) == 0:
                merit = 1.0
            else:
                merit = float(np.prod([m(start, task, data) for m in task.merits]))
        merits.append(merit)
    return merits


def find_next_best_task(tasks: list[Task], start: Time, end: Time, data: DataProvider) -> tuple[Task | None, float]:
    # evaluate all merit functions at given time
    merits = evaluate_merits(tasks, start, end, data)

    # find max one
    idx = np.argmax(merits)
    task = tasks[idx]

    # if merit is zero, return nothing
    return None if merits[idx] == 0.0 else task, merits[idx]


def check_for_better_task(
    task: Task, merit: float, tasks: list[Task], start: Time, end: Time, data: DataProvider, step: float = 300
) -> tuple[Task | None, Time | None, float | None]:
    t = start + TimeDelta(step * u.second)
    while t < start + TimeDelta(task.duration):
        merits = evaluate_merits(tasks, t, end, data)
        for i, m in enumerate(merits):
            if m > merit:
                return tasks[i], t, m
        t += TimeDelta(step * u.second)
    return None, None, None


def can_postpone_task(
    task: Task, better_task: Task, better_merit: float, start: Time, end: Time, data: DataProvider
) -> Time | None:
    # new start time of better_task would be after the execution of task
    better_start: Time = start + TimeDelta(task.duration)

    # evaluate merit of better_task at new start time
    merit = evaluate_merits([better_task], better_start, end, data)[0]

    # if it got better, return it, otherwise return Nones
    if merit >= better_merit:
        return better_start
    else:
        return None


__all__ = ["MeritScheduler"]
