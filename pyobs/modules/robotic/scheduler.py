from __future__ import annotations
import asyncio
import json
import logging
import time
from typing import Union, Any, Dict

from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.events import GoodWeatherEvent, Event
from pyobs.robotic.scheduler import TaskScheduler
from pyobs.utils.time import Time
from pyobs.interfaces import IStartStop, IRunnable
from pyobs.modules import Module
from pyobs.robotic import TaskArchive, TaskSchedule, ScheduledTask, Task

log = logging.getLogger(__name__)


class Scheduler(Module, IStartStop, IRunnable):
    """Scheduler."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scheduler: dict[str, Any] | TaskScheduler,
        tasks: Union[Dict[str, Any], TaskArchive],
        schedule: Union[Dict[str, Any], TaskSchedule],
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
        self._scheduler = self.add_child_object(scheduler, TaskScheduler)
        self._task_archive = self.add_child_object(tasks, TaskArchive)
        self._schedule = self.add_child_object(schedule, TaskSchedule)

        # store
        self._running = True
        self._initial_update_done = False
        self._need_update = False
        self._trigger_on_task_started = trigger_on_task_started
        self._trigger_on_task_finished = trigger_on_task_finished

        # time to start next schedule from
        self._schedule_start: Time = Time.now()

        # ID of currently running task, and current (or last if finished) block
        self._current_task_id = None
        self._last_task_id = None

        # tasks
        self._tasks: list[Task] = []

        # update thread
        self.add_background_task(self._schedule_worker)
        self.add_background_task(self._update_worker)

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
        self._running = True

    async def stop(self, **kwargs: Any) -> None:
        """Stop scheduler."""
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether scheduler is running."""
        return self._running

    async def _update_worker(self) -> None:
        # time of last change in blocks
        last_change = None

        # run forever
        while True:
            # not running?
            if not self._running:
                await asyncio.sleep(1)
                continue

            # got new time of last change?
            t = await self._task_archive.last_changed()
            if last_change is None or last_change < t:
                # get schedulable tasks and sort them
                log.info("Found update in schedulable tasks, downloading them...")
                tasks = sorted(
                    await self._task_archive.get_schedulable_tasks(),
                    key=lambda x: json.dumps(x.id, sort_keys=True),
                )
                log.info("Downloaded %d schedulable tasks(s).", len(tasks))

                # compare new and old lists
                removed, added = self._compare_task_lists(self._tasks, tasks)

                # schedule update
                self._need_update = True

                # no changes?
                if len(removed) == 0 and len(added) == 0:
                    # no need to re-schedule
                    log.info("No change in list of blocks detected.")
                    self._need_update = False

                # has only the current block been removed?
                log.info("Removed: %d, added: %d", len(removed), len(added))
                if len(removed) == 1:
                    log.info(
                        "Found 1 removed block with ID %d. Last task ID was %s, current is %s.",
                        removed[0].id,
                        str(self._last_task_id),
                        str(self._current_task_id),
                    )
                if len(removed) == 1 and len(added) == 0 and removed[0].id == self._last_task_id:
                    # no need to re-schedule
                    log.info("Only one removed block detected, which is the one currently running.")
                    self._need_update = False

                # check, if one of the removed blocks was actually in schedule
                if len(removed) > 0 and self._need_update:
                    schedule = await self._schedule.get_schedule()
                    removed_from_schedule = [r for r in removed if r in schedule]
                    if len(removed_from_schedule) == 0:
                        log.info(f"Found {len(removed)} blocks, but none of them was scheduled.")
                        self._need_update = False

                # store blocks
                self._tasks = tasks

                # schedule update
                if self._need_update:
                    log.info("Triggering scheduler run...")

                # remember now
                last_change = Time.now()
                self._initial_update_done = True

            # sleep a little
            await asyncio.sleep(5)

    @staticmethod
    def _compare_task_lists(tasks1: list[Task], tasks2: list[Task]) -> tuple[list[Task], list[Task]]:
        """Compares two lists of tasks and returns two lists, containing those that are missing in list 1
        and list 2, respectively.

        Args:
            tasks1: First list of tasks.
            tasks2: Second list of tasks.

        Returns:
            (tuple): Tuple containing:
                unique1:  Blocks that exist in tasks1, but not in tasks2.
                unique2:  Blocks that exist in tasks2, but not in tasks1.
        """

        # get dictionaries with block names
        names1 = {t.id: t for t in tasks1}
        names2 = {t.id: t for t in tasks2}

        # find elements in names1 that are missing in names2 and vice versa
        additional1 = set(names1.keys()).difference(names2.keys())
        additional2 = set(names2.keys()).difference(names1.keys())

        # get blocks for names and return them
        unique1 = [names1[n] for n in additional1]
        unique2 = [names2[n] for n in additional2]
        return unique1, unique2

    async def _schedule_worker(self) -> None:
        # run forever
        while True:
            # need update?
            if self._need_update and self._initial_update_done:
                # reset need for update
                self._need_update = False

                try:

                    # start time
                    start_time = time.time()

                    # schedule
                    scheduled_tasks = await self._scheduler.schedule(self._tasks, self._schedule_start)

                    # upload schedule
                    await self._finish_schedule(scheduled_tasks)

                    # set new safety_time as duration + 20%
                    self._safety_time = (time.time() - start_time) * 1.2

                except:
                    log.exception("Something went wrong")

            # sleep a little
            await asyncio.sleep(1)

    async def _finish_schedule(self, scheduled_tasks: list[ScheduledTask]) -> None:
        # if need new update, skip here
        if self._need_update:
            log.info("Not using scheduler results, since update was requested.")
            return

        # update
        # await self._schedule.set_schedule(scheduled_tasks, start)

        # log
        if len(scheduled_tasks) > 0:
            log.info("Finished calculating schedule for %d block(s):", len(scheduled_tasks))
            for i, scheduled_task in enumerate(scheduled_tasks, 1):
                log.info(
                    "  - %s to %s: %s (%d)",
                    scheduled_task.start.strftime("%H:%M:%S"),
                    scheduled_task.end.strftime("%H:%M:%S"),
                    scheduled_task.task.name,
                    scheduled_task.task.id,
                )
        else:
            log.info("Finished calculating schedule for 0 blocks.")

    async def run(self, **kwargs: Any) -> None:
        """Trigger a re-schedule."""
        self._need_update = True

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

        # trigger?
        if self._trigger_on_task_started:
            # get ETA in minutes
            eta = (event.eta - Time.now()).sec / 60
            log.info("Received task started event with ETA of %.0f minutes, triggering new scheduler run...", eta)

            # set it
            self._need_update = True
            self._schedule_start = event.eta

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

            # set it
            self._need_update = True
            self._schedule_start = Time.now()

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

        # set it
        self._need_update = True
        self._schedule_start = event.eta
        return True

    async def abort(self, **kwargs: Any) -> None:
        pass


__all__ = ["Scheduler"]
