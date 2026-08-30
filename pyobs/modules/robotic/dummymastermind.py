from __future__ import annotations

import asyncio
import itertools
import logging
import random
from typing import Any

import astropy.units as u

from pyobs.events import TaskFailedEvent, TaskFinishedEvent, TaskStartedEvent
from pyobs.interfaces import IAutonomous, IRobotic, IRunning, RoboticState, RoboticTask
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyMastermind(Module, IAutonomous, IRobotic):
    """Dummy executor that simulates a robotic schedule for pyobs-gui development.

    Generates and runs a synthetic sequence of tasks, occasionally with a simulated
    "can't run" wait beforehand and an occasional failure, so `RoboticWidget` has real state
    transitions to develop against without needing a real `ObservationArchive`/`TaskRunner`.
    Independent of `DummyScheduler` -- the two don't share any synthetic data.
    """

    __module__ = "pyobs.modules.robotic"

    _TARGETS = ["M31", "M42", "NGC 891", "Vega", "HD 12345", "IC 1805", "Altair"]
    _KINDS = ["Photometry", "Spectroscopy", "Flatfields", "Focus series"]
    _BLOCK_REASONS = ["waiting for weather", "target below horizon", "window not open yet"]

    def __init__(
        self,
        min_duration: float = 30.0,
        max_duration: float = 180.0,
        fail_probability: float = 0.15,
        blocked_probability: float = 0.2,
        min_blocked_duration: float = 5.0,
        max_blocked_duration: float = 20.0,
        **kwargs: Any,
    ):
        """Create a new dummy mastermind.

        Args:
            min_duration: Minimum simulated task duration, in seconds.
            max_duration: Maximum simulated task duration, in seconds.
            fail_probability: Chance [0, 1] that a simulated task run ends in failure.
            blocked_probability: Chance [0, 1] that the next task simulates a "can't run" wait
                before starting.
            min_blocked_duration: Minimum simulated "can't run" wait, in seconds.
            max_blocked_duration: Maximum simulated "can't run" wait, in seconds.
        """
        Module.__init__(self, **kwargs)

        self._min_duration = min_duration
        self._max_duration = max_duration
        self._fail_probability = fail_probability
        self._blocked_probability = blocked_probability
        self._min_blocked_duration = min_blocked_duration
        self._max_blocked_duration = max_blocked_duration

        self._running = False
        self._task_ids = itertools.count(1)
        self._task: RoboticTask | None = None  # currently running

        self.add_background_task(self._run_thread, True)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        if self._comm:
            await self.comm.register_event(TaskStartedEvent)
            await self.comm.register_event(TaskFinishedEvent)

        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish()

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        log.info("Starting dummy robotic system...")
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish()

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        log.info("Stopping dummy robotic system...")
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish()

    def _make_task(self) -> RoboticTask:
        return RoboticTask(
            id=next(self._task_ids),
            name=f"{random.choice(self._KINDS)}-{random.choice(self._TARGETS)}",
            target=random.choice(self._TARGETS),
            priority=round(random.uniform(1.0, 10.0), 1),
        )

    async def _publish(self, next_task: RoboticTask | None = None, cant_run_reason: str | None = None) -> None:
        await self.comm.set_state(
            IRobotic, RoboticState(current=self._task, next=next_task, cant_run_reason=cant_run_reason)
        )

    async def _run_thread(self) -> None:
        await asyncio.sleep(2)

        while True:
            if not self._running:
                await asyncio.sleep(1)
                continue

            next_task = self._make_task()

            # occasionally simulate a "can't run yet" wait before this task starts
            if random.random() < self._blocked_probability:
                reason = random.choice(self._BLOCK_REASONS)
                log.info("Task %s cannot run: %s", next_task.name, reason)
                await self._publish(next_task=next_task, cant_run_reason=reason)
                blocked_for = random.uniform(self._min_blocked_duration, self._max_blocked_duration)
                await asyncio.sleep(blocked_for)

            # start it
            start = Time.now()
            duration = random.uniform(self._min_duration, self._max_duration)
            end = start + duration * u.second
            next_task.start = start
            next_task.end = end
            next_task.state = "in_progress"
            self._task = next_task

            log.info("Running task %s...", next_task.name)
            await self.comm.send_event(TaskStartedEvent(name=next_task.name, id=next_task.id, eta=end))
            await self._publish()

            await asyncio.sleep(duration)

            if random.random() < self._fail_probability:
                self._task.state = "failed"
                log.info("Task %s failed.", next_task.name)
                await self.comm.send_event(TaskFailedEvent(name=next_task.name, id=next_task.id))
            else:
                self._task.state = "completed"
                log.info("Finished task %s.", next_task.name)
                await self.comm.send_event(TaskFinishedEvent(name=next_task.name, id=next_task.id))

            self._task = None
            await self._publish()


__all__ = ["DummyMastermind"]
