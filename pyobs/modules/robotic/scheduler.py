import asyncio
import copy
import json
import logging
import multiprocessing as mp
from typing import Union, List, Tuple, Any, Optional, Dict, cast
import astroplan
import astropy
from astroplan import ObservingBlock
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.events import GoodWeatherEvent, Event
from pyobs.modules.robotic._taskscheduler import _TaskScheduler
from pyobs.modules.robotic._taskupdater import _TaskUpdater
from pyobs.utils.time import Time
from pyobs.interfaces import IStartStop, IRunnable
from pyobs.modules import Module
from pyobs.robotic import TaskArchive, TaskSchedule, Task

log = logging.getLogger(__name__)


class Scheduler(Module, IStartStop, IRunnable):
    """Scheduler."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        tasks: Union[Dict[str, Any], TaskArchive],
        schedule: Union[Dict[str, Any], TaskSchedule],
        schedule_range: int = 24,
        safety_time: int = 60,
        twilight: str = "astronomical",
        trigger_on_task_started: bool = False,
        trigger_on_task_finished: bool = False,
        **kwargs: Any,
    ):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use
            schedule_range: Number of hours to schedule into the future
            safety_time: If no ETA for next task to start exists (from current task, weather became good, etc), use
                         this time in seconds to make sure that we don't schedule for a time when the scheduler is
                         still running
            twilight: astronomical or nautical
            trigger_on_task_started: Whether to trigger a re-calculation of schedule, when task has started.
            trigger_on_task_finishes: Whether to trigger a re-calculation of schedule, when task has finished.
        """
        Module.__init__(self, **kwargs)

        # get scheduler
        self._task_archive = self.add_child_object(tasks, TaskArchive)  # type: ignore
        self._schedule = self.add_child_object(schedule, TaskSchedule)  # type: ignore

        # store
        #self._schedule_range = schedule_range
        #self._safety_time = safety_time
        #self._twilight = twilight

        self._trigger_on_task_started = trigger_on_task_started
        self._trigger_on_task_finished = trigger_on_task_finished

        # time to start next schedule from
        #self._schedule_start: Optional[Time] = None

        # ID of currently running task, and current (or last if finished) block
        #self._current_task_id = None
        #self._last_task_id = None

        # blocks
        self._blocks: List[ObservingBlock] = []

        self._task_updater = _TaskUpdater(self._task_archive, self._schedule)
        self._task_scheduler = _TaskScheduler(self._schedule, self.observer, schedule_range, safety_time, twilight)

        # update thread
        self._scheduler_task = self.add_background_task(self._task_scheduler.schedule_task, autostart=False, restart=False)
        self._update_task = self.add_background_task(self._update_worker)

        self._last_change: Optional[Time] = None

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self.comm:
            await self.comm.register_event(TaskStartedEvent, self._on_task_started)
            await self.comm.register_event(TaskFinishedEvent, self._on_task_finished)
            await self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

    async def start(self, **kwargs: Any) -> None:
        """Start scheduler."""
        self._update_task.start()

    async def stop(self, **kwargs: Any) -> None:
        """Stop scheduler."""
        self._update_task.stop()

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether scheduler is running."""
        return self._update_task.is_running()

    async def _update_worker(self) -> None:
        while True:
            await self._update_worker_loop()
            await asyncio.sleep(5)

    async def _update_worker_loop(self) -> None:
        blocks = await self._task_updater.update()

        if blocks is None:
            return

        self._scheduler_task.stop()
        self._task_scheduler.set_blocks(blocks)
        self._scheduler_task.start()

    async def run(self, **kwargs: Any) -> None:
        """Trigger a re-schedule."""
        self._scheduler_task.stop()
        self._scheduler_task.start()

    async def _on_task_started(self, event: Event, sender: str) -> bool:
        """Re-schedule when task has started and we can predict its end.

        Args:
            event: The task started event.
            sender: Who sent it.
        """
        if not isinstance(event, TaskStartedEvent):
            return False

        # store it
        self._task_scheduler.set_current_task_id(event.id)
        self._task_updater.set_current_task_id(event.id)
        self._task_updater.set_last_task_id(event.id)

        # trigger?
        if self._trigger_on_task_started:
            # get ETA in minutes
            eta = (event.eta - Time.now()).sec / 60
            log.info("Received task started event with ETA of %.0f minutes, triggering new scheduler run...", eta)

            self._scheduler_task.stop()
            self._scheduler_task.start()
            self._schedule_start = event.eta
            self._task_scheduler.set_schedule_start(event.eta)

        return True

    async def _on_task_finished(self, event: Event, sender: str) -> bool:
        """Reset current task, when it has finished.

        Args:
            event: The task finished event.
            sender: Who sent it.
        """
        if not isinstance(event, TaskFinishedEvent):
            return False

        # reset current task
        self._task_scheduler.set_current_task_id(None)
        self._task_updater.set_current_task_id(None)

        # trigger?
        if self._trigger_on_task_finished:
            # get ETA in minutes
            log.info("Received task finished event, triggering new scheduler run...")

            self._scheduler_task.stop()
            self._scheduler_task.start()
            self._schedule_start = Time.now()
            self._task_scheduler.set_schedule_start(Time.now())

        return True

    async def _on_good_weather(self, event: Event, sender: str) -> bool:
        """Re-schedule on incoming good weather event.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """
        if not isinstance(event, GoodWeatherEvent):
            return False

        # get ETA in minutes
        eta = (event.eta - Time.now()).sec / 60
        log.info("Received good weather event with ETA of %.0f minutes, triggering new scheduler run...", eta)

        self._scheduler_task.stop()
        self._scheduler_task.start()
        self._schedule_start = event.eta
        self._task_scheduler.set_schedule_start(event.eta)
        return True

    async def abort(self, **kwargs: Any) -> None:
        pass


__all__ = ["Scheduler"]
