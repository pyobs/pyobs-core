from __future__ import annotations

import asyncio
import dataclasses
import itertools
import logging
import random
from typing import Any

import astropy.units as u

from pyobs.interfaces import IRoboticScheduler, IRunnable, IRunning, RoboticTask, SchedulerState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyScheduler(Module, IRunnable, IRoboticScheduler):
    """Dummy planner that simulates a schedule for pyobs-gui development.

    Generates a synthetic, contiguous batch of upcoming tasks on open() and whenever run() is
    called ("Re-schedule now"), so `ScheduleWidget` has real data and a working re-schedule
    button to develop against without needing a real `TaskArchive`/`ObservationArchive`/
    `TaskScheduler`. Independent of `DummyMastermind` -- the two don't share any synthetic data.
    """

    __module__ = "pyobs.modules.robotic"

    _MAX_SCHEDULE_LIMIT = 100

    _TARGETS = ["M31", "M42", "NGC 891", "Vega", "HD 12345", "IC 1805", "Altair"]
    _KINDS = ["Photometry", "Spectroscopy", "Flatfields", "Focus series"]

    def __init__(
        self,
        schedule_size: int = 8,
        min_duration: float = 60.0,
        max_duration: float = 600.0,
        **kwargs: Any,
    ):
        """Create a new dummy scheduler.

        Args:
            schedule_size: Number of synthetic tasks to generate per (re-)schedule.
            min_duration: Minimum simulated task duration, in seconds.
            max_duration: Maximum simulated task duration, in seconds.
        """
        Module.__init__(self, **kwargs)

        self._schedule_size = schedule_size
        self._min_duration = min_duration
        self._max_duration = max_duration

        self._running = True
        self._last_reschedule: Time | None = None
        self._task_ids = itertools.count(1)
        self._schedule: list[RoboticTask] = []
        self._need_update = True

        self.add_background_task(self._schedule_worker)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # generate the first schedule synchronously, rather than waiting for the worker's first
        # tick, so get_schedule() has something to return immediately on startup
        self._generate_schedule()
        self._last_reschedule = Time.now()
        self._need_update = False

        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def start(self, **kwargs: Any) -> None:
        """Start scheduler."""
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def stop(self, **kwargs: Any) -> None:
        """Stop scheduler."""
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def run(self, **kwargs: Any) -> None:
        """Trigger a re-schedule."""
        self._need_update = True

    async def abort(self, **kwargs: Any) -> None:
        pass

    def _generate_schedule(self) -> None:
        cursor = Time.now()
        tasks = []
        for _ in range(self._schedule_size):
            duration = random.uniform(self._min_duration, self._max_duration)
            start = cursor
            end = start + duration * u.second
            tasks.append(
                RoboticTask(
                    id=next(self._task_ids),
                    name=f"{random.choice(self._KINDS)}-{random.choice(self._TARGETS)}",
                    target=random.choice(self._TARGETS),
                    start=start,
                    end=end,
                    state="pending",
                    priority=round(random.uniform(1.0, 10.0), 1),
                )
            )
            cursor = end
        self._schedule = tasks

    async def _schedule_worker(self) -> None:
        while True:
            if self._running and self._need_update:
                self._need_update = False
                log.info("Generating dummy schedule of %d task(s)...", self._schedule_size)
                self._generate_schedule()
                self._last_reschedule = Time.now()
                await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))
            await asyncio.sleep(1)

    async def get_schedule(self, limit: int = 20, **kwargs: Any) -> list[RoboticTask]:
        """Return the upcoming (pending/in-progress) synthetic schedule, most imminent first.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            Up to `limit` scheduled tasks, capped at `_MAX_SCHEDULE_LIMIT` regardless of what's
            requested.

        Raises:
            ValueError: If limit is not an int, or is negative.
        """
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative int.")
        limit = min(limit, self._MAX_SCHEDULE_LIMIT)

        now = Time.now()
        upcoming = []
        for task in sorted(self._schedule, key=lambda t: t.start or now):
            if task.end is not None and task.end < now:
                continue  # already elapsed
            state = "in_progress" if task.start is not None and task.start <= now else "pending"
            upcoming.append(dataclasses.replace(task, state=state))

        return upcoming[:limit]


__all__ = ["DummyScheduler"]
