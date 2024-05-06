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
        self._current_task_id = None
        self._last_task_id = None

        # blocks
        self._blocks: List[ObservingBlock] = []

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
        # got new time of last change?
        t = await self._task_archive.last_changed()
        if self._last_change is None or self._last_change < t:
            await self._update_blocks()

            self._last_change = Time.now()

    async def _update_blocks(self) -> None:
        # get schedulable blocks and sort them
        log.info("Found update in schedulable block, downloading them...")
        blocks = sorted(
            await self._task_archive.get_schedulable_blocks(),
            key=lambda x: json.dumps(x.configuration, sort_keys=True),
        )
        log.info("Downloaded %d schedulable block(s).", len(blocks))

        # compare new and old lists
        removed, added = self._compare_block_lists(self._blocks, blocks)

        # store blocks
        self._blocks = blocks
        self._task_scheduler.set_blocks(blocks)

        # schedule update
        if await self._need_update(removed, added):
            log.info("Triggering scheduler run...")
            self._scheduler_task.stop()     # Stop current run
            self._scheduler_task.start()

    async def _need_update(self, removed: List[ObservingBlock], added: List[ObservingBlock]) -> bool:
        if len(removed) == 0 and len(added) == 0:
            # no need to re-schedule
            log.info("No change in list of blocks detected.")
            return False

        # has only the current block been removed?
        log.info("Removed: %d, added: %d", len(removed), len(added))
        if len(removed) == 1:
            log.info(
                "Found 1 removed block with ID %d. Last task ID was %s, current is %s.",
                removed[0].target.name,
                str(self._last_task_id),
                str(self._current_task_id),
            )
        if len(removed) == 1 and len(added) == 0 and removed[0].target.name == self._last_task_id:
            # no need to re-schedule
            log.info("Only one removed block detected, which is the one currently running.")
            return False

        # check, if one of the removed blocks was actually in schedule
        if len(removed) > 0:
            schedule = await self._schedule.get_schedule()
            removed_from_schedule = [r for r in removed if r in schedule]
            if len(removed_from_schedule) == 0:
                log.info(f"Found {len(removed)} blocks, but none of them was scheduled.")
                return False

        return True

    @staticmethod
    def _compare_block_lists(
        blocks1: List[ObservingBlock], blocks2: List[ObservingBlock]
    ) -> Tuple[List[ObservingBlock], List[ObservingBlock]]:
        """Compares two lists of ObservingBlocks and returns two lists, containing those that are missing in list 1
        and list 2, respectively.

        Args:
            blocks1: First list of blocks.
            blocks2: Second list of blocks.

        Returns:
            (tuple): Tuple containing:
                unique1:  Blocks that exist in blocks1, but not in blocks2.
                unique2:  Blocks that exist in blocks2, but not in blocks1.
        """

        # get dictionaries with block names
        names1 = {b.target.name: b for b in blocks1}
        names2 = {b.target.name: b for b in blocks2}

        # find elements in names1 that are missing in names2 and vice versa
        additional1 = set(names1.keys()).difference(names2.keys())
        additional2 = set(names2.keys()).difference(names1.keys())

        # get blocks for names and return them
        unique1 = [names1[n] for n in additional1]
        unique2 = [names2[n] for n in additional2]
        return unique1, unique2

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
        self._current_task_id = event.id
        self._last_task_id = event.id
        self._task_scheduler.set_current_task_id(event.id)

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
        self._current_task_id = None

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
