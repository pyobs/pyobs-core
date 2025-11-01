from __future__ import annotations
import asyncio
import logging
from typing import Any, TYPE_CHECKING

from pyobs.object import Object
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

    async def schedule(self, tasks: list[Task], start: Time) -> list[ScheduledTask]:
        return []

    async def abort(self) -> None:
        self._abort.set()


__all__ = ["MeritScheduler"]
