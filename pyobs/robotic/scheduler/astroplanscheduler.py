from __future__ import annotations
import asyncio
import logging
import multiprocessing as mp
from typing import Any, TYPE_CHECKING
from collections.abc import AsyncIterator
import astroplan
from astroplan import ObservingBlock, FixedTarget

from pyobs.object import Object
from .taskscheduler import TaskScheduler
from .targets import SiderealTarget
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import ScheduledTask, Task

log = logging.getLogger(__name__)


class AstroplanScheduler(TaskScheduler):
    """Scheduler based on astroplan."""

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
        self._lock = asyncio.Lock()
        self._abort: asyncio.Event = asyncio.Event()
        self._is_running: bool = False

    async def schedule(self, tasks: list[Task], start: Time, end: Time) -> AsyncIterator[ScheduledTask]:
        # is lock acquired? send abort signal
        if self._lock.locked():
            await self.abort()

        # get lock
        async with self._lock:
            # prepare scheduler
            blocks, start, end, constraints = await self._prepare_schedule(tasks, start, end)

            # schedule
            scheduled_blocks = await self._schedule_blocks(blocks, start, end, constraints, self._abort)

            # convert
            scheduled_tasks = await self._convert_blocks(scheduled_blocks, tasks)

            # yield them
            for scheduled_task in scheduled_tasks:
                yield scheduled_task

            # clean up
            del blocks, constraints, scheduled_blocks, scheduled_tasks

    async def abort(self) -> None:
        self._abort.set()

    async def _prepare_schedule(
        self, tasks: list[Task], start: Time, end: Time
    ) -> tuple[list[ObservingBlock], Time, Time, list[Any]]:
        """TaskSchedule blocks."""

        # only global constraint is the night
        if self._twilight == "astronomical":
            constraints = [astroplan.AtNightConstraint.twilight_astronomical()]
        elif self._twilight == "nautical":
            constraints = [astroplan.AtNightConstraint.twilight_nautical()]
        else:
            raise ValueError("Unknown twilight type.")

        # create blocks from tasks
        blocks: list[ObservingBlock] = []
        for task in tasks:
            target = task.target
            if not isinstance(target, SiderealTarget):
                log.warning("Non-sidereal targets not supported.")
                continue

            priority = 1000.0 - task.priority
            if priority < 0:
                priority = 0

            blocks.append(
                ObservingBlock(
                    FixedTarget(target.coord, name=target.name),
                    task.duration,
                    priority,
                    constraints=[c.to_astroplan() for c in task.constraints] if task.constraints else None,
                    configuration={"request": task.config},
                    name=task.id,
                )
            )

        # return all
        return blocks, start, end, constraints

    async def _schedule_blocks(
        self, blocks: list[ObservingBlock], start: Time, end: Time, constraints: list[Any], abort: asyncio.Event
    ) -> list[ObservingBlock]:

        # run actual scheduler in separate process and wait for it
        queue_out: mp.Queue[ObservingBlock] = mp.Queue()
        p = mp.Process(target=self._schedule_process, args=(blocks, start, end, constraints, queue_out))
        p.start()

        # wait for process to finish
        # note that the process only finishes, when the queue is empty! so we have to poll the queue first
        # and then the process.
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, queue_out.get, True)
        while not future.done():
            if abort.is_set():
                p.kill()
                return []
            else:
                await asyncio.sleep(0.1)
        scheduled_blocks: list[ObservingBlock] = await future
        await loop.run_in_executor(None, p.join)

        return scheduled_blocks

    def _schedule_process(
        self,
        blocks: list[ObservingBlock],
        start: Time,
        end: Time,
        constraints: list[Any],
        scheduled_blocks: mp.Queue[ObservingBlock],
    ) -> None:
        """Actually do the scheduling, usually run in a separate process."""

        # log it
        log.info("Calculating schedule for %d schedulable block(s) starting at %s...", len(blocks), start)

        # we don't need any transitions
        transitioner = astroplan.Transitioner()

        # create scheduler
        scheduler = astroplan.PriorityScheduler(constraints, self.observer, transitioner=transitioner)

        # run scheduler
        logging.disable(logging.WARNING)
        time_range = astroplan.Schedule(start, end)
        schedule = scheduler(blocks, time_range)
        logging.disable(logging.NOTSET)

        # put scheduled blocks in queue
        scheduled_blocks.put(schedule.scheduled_blocks)

        # clean up
        del transitioner, scheduler, schedule

    async def _convert_blocks(self, blocks: list[ObservingBlock], tasks: list[Task]) -> list[ScheduledTask]:
        from pyobs.robotic import ScheduledTask

        scheduled_tasks: list[ScheduledTask] = []
        for block in blocks:
            # find task
            task_id = block.name
            for task in tasks:
                if task.id == task_id:
                    break
            else:
                raise ValueError(f"Could not find task with id '{task_id}'")

            # create scheduled task
            scheduled_tasks.append(ScheduledTask(task, block.start_time, block.end_time))

        return scheduled_tasks


__all__ = ["AstroplanScheduler"]
