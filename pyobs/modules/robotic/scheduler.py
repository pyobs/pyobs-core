import asyncio
import copy
import json
import logging
import multiprocessing as mp
from typing import Union, List, Tuple, Any
from astroplan import AtNightConstraint, Transitioner, Schedule, TimeConstraint, ObservingBlock, PriorityScheduler
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.events import GoodWeatherEvent, Event
from pyobs.utils.time import Time
from pyobs.interfaces import IStartStop, IRunnable
from pyobs.modules import Module
from pyobs.robotic import TaskArchive


log = logging.getLogger(__name__)


class Scheduler(Module, IStartStop, IRunnable):
    """Scheduler."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        tasks: Union[dict, TaskArchive],
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
        self._task_archive = self.add_child_object(tasks, TaskArchive)

        # store
        self._schedule_range = schedule_range
        self._safety_time = safety_time
        self._twilight = twilight
        self._running = True
        self._initial_update_done = False
        self._need_update = False
        self._trigger_on_task_started = trigger_on_task_started
        self._trigger_on_task_finished = trigger_on_task_finished

        # time to start next schedule from
        self._schedule_start = None

        # ID of currently running task, and current (or last if finished) block
        self._current_task_id = None
        self._last_task_id = None

        # blocks
        self._blocks: List[ObservingBlock] = []

        # update thread
        self.add_background_task(self._schedule_thread)
        self.add_background_task(self._update_thread)

    async def open(self):
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self.comm:
            await self.comm.register_event(TaskStartedEvent, self._on_task_started)
            await self.comm.register_event(TaskFinishedEvent, self._on_task_finished)
            await self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

    async def start(self, **kwargs: Any):
        """Start scheduler."""
        self._running = True

    async def stop(self, **kwargs: Any):
        """Stop scheduler."""
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether scheduler is running."""
        return self._running

    async def _update_thread(self):
        # time of last change in blocks
        last_change = None

        # run forever
        while True:
            # not running?
            if self._running is False:
                await asyncio.sleep(1)
                continue

            # got new time of last change?
            t = await self._task_archive.last_changed()
            if last_change is None or last_change < t:
                # get schedulable blocks and sort them
                log.info("Found update in schedulable block, downloading them...")
                blocks = sorted(
                    await self._task_archive.get_schedulable_blocks(),
                    key=lambda x: json.dumps(x.configuration, sort_keys=True),
                )
                log.info("Downloaded %d schedulable block(s).", len(blocks))

                # compare new and old lists
                removed, added = Scheduler._compare_block_lists(self._blocks, blocks)

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
                        removed[0].target.name,
                        str(self._last_task_id),
                        str(self._current_task_id),
                    )
                if len(removed) == 1 and len(added) == 0 and removed[0].target.name == self._last_task_id:
                    # no need to re-schedule
                    log.info("Only one removed block detected, which is the one currently running.")
                    self._need_update = False

                # store blocks
                self._blocks = blocks

                # schedule update
                if self._need_update:
                    log.info("Triggering scheduler run...")

                # remember now
                last_change = Time.now()
                self._initial_update_done = True

            # sleep a little
            await asyncio.sleep(5)

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

    async def _schedule_thread(self):
        # run forever
        while True:
            # need update?
            if self._need_update and self._initial_update_done:
                # reset need for update
                self._need_update = False

                # run scheduler in separate process and wait for it
                p = mp.Process(target=self._schedule_process)
                p.start()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, p.join)

            # sleep a little
            await asyncio.sleep(1)

    def _schedule_process(self):
        """This is run in a new process and starts a new loop running the _schedule method."""
        asyncio.run(self._schedule())

    async def _schedule(self):
        """Actually do the scheduling, usually run in a separate process."""

        # only global constraint is the night
        if self._twilight == "astronomical":
            constraints = [AtNightConstraint.twilight_astronomical()]
        elif self._twilight == "nautical":
            constraints = [AtNightConstraint.twilight_nautical()]
        else:
            raise ValueError("Unknown twilight type.")

        # make shallow copies of all blocks and loop them
        copied_blocks = [copy.copy(block) for block in self._blocks]
        for block in copied_blocks:
            # astroplan's PriorityScheduler expects lower priorities to be more important, so calculate
            # 1000 - priority
            block.priority = 1000.0 - block.priority
            if block.priority < 0:
                block.priority = 0

            # it also doesn't match the requested observing windows exactly, so we make them a little smaller.
            for constraint in block.constraints:
                if isinstance(constraint, TimeConstraint):
                    constraint.min += 30 * u.second
                    constraint.max -= 30 * u.second

        # get start time for scheduler
        start = self._schedule_start
        now_plus_safety = Time.now() + self._safety_time * u.second
        if start is None or start < now_plus_safety:
            # if no ETA exists or is in the past, use safety time
            start = now_plus_safety

        # get running scheduled block, if any
        if self._current_task_id is None:
            log.info("No running block found.")
            running_task = None
        else:
            # get running task from archive
            log.info("Trying to find running block in current schedule...")
            now = Time.now()
            tasks = await self._task_archive.get_pending_tasks(now, now, include_running=True)
            if self._current_task_id in tasks:
                running_task = tasks[self._current_task_id]
            else:
                log.info("Running block not found in last schedule.")
                running_task = None

        # if start is before end time of currently running block, change that
        if running_task is not None:
            log.info("Found running block that ends at %s.", running_task.end)

            # get block end plus some safety
            block_end = running_task.end + 10.0 * u.second
            if start < block_end:
                start = block_end
                log.info("Start time would be within currently running block, shifting to %s.", start.isot)

        # calculate end time
        end = start + TimeDelta(self._schedule_range * u.hour)

        # remove currently running block and filter by start time
        blocks = []
        for b in filter(lambda x: x.configuration["request"]["id"] != self._current_task_id, copied_blocks):
            time_constraint_found = False
            # loop all constraints
            for c in b.constraints:
                if isinstance(c, TimeConstraint):
                    # we found a time constraint
                    time_constraint_found = True

                    # does the window start before the end of the scheduling range?
                    if c.min < end:
                        # yes, store block and break loop
                        blocks.append(b)
                        break
            else:
                # loop has finished without breaking
                # if no time constraint has been found, we still take the block
                if time_constraint_found is False:
                    blocks.append(b)

        # if need new update, skip here
        if self._need_update:
            log.info("Not running scheduler, since update was requested.")
            return

        # no blocks found?
        if len(blocks) == 0:
            log.info("No blocks left for scheduling.")
            await self._task_archive.update_schedule([], start)
            return

        # log it
        log.info("Calculating schedule for %d schedulable block(s) starting at %s...", len(blocks), start)

        # we don't need any transitions
        transitioner = Transitioner()

        # create scheduler
        scheduler = PriorityScheduler(constraints, self.observer, transitioner=transitioner)

        # run scheduler
        time_range = Schedule(start, end)
        loop = asyncio.get_running_loop()
        schedule = await loop.run_in_executor(None, scheduler, blocks, time_range)

        # if need new update, skip here
        if self._need_update:
            log.info("Not using scheduler results, since update was requested.")
            return

        # update
        await self._task_archive.update_schedule(schedule.scheduled_blocks, start)
        if len(schedule.scheduled_blocks) > 0:
            log.info("Finished calculating schedule for %d block(s):", len(schedule.scheduled_blocks))
            for i, block in enumerate(schedule.scheduled_blocks, 1):
                log.info(
                    "  #%d: %s to %s (%.1f)",
                    block.configuration["request"]["id"],
                    block.start_time.strftime("%H:%M:%S"),
                    block.end_time.strftime("%H:%M:%S"),
                    block.priority,
                )
        else:
            log.info("Finished calculating schedule for 0 blocks.")

    async def run(self, **kwargs: Any):
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
