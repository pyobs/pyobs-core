from __future__ import annotations
import asyncio
import logging
import multiprocessing as mp
from typing import Any
import astroplan
from astroplan import ObservingBlock, FixedTarget
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.object import Object
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time
from pyobs.robotic import ScheduledTask, Task

log = logging.getLogger(__name__)


class AstroplanScheduler(Object):
    """Scheduler based on astroplan."""

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

    async def schedule(self, tasks: list[Task], start: Time) -> list[ScheduledTask]:
        # prepare scheduler
        blocks, start, end, constraints = await self._prepare_schedule(tasks, start)

        # schedule
        scheduled_blocks = await self._schedule_blocks(blocks, start, end, constraints)
        scheduled_blocks.sort(key=lambda b: b.time)  # remove

        # TODO: add abort (see old robotic/scheduler.py)

        return []

    async def _prepare_schedule(
        self, tasks: list[Task], start: Time
    ) -> tuple[list[ObservingBlock], Time, Time, list[Any]]:
        """TaskSchedule blocks."""

        # only global constraint is the night
        if self._twilight == "astronomical":
            constraints = [astroplan.AtNightConstraint.twilight_astronomical()]
        elif self._twilight == "nautical":
            constraints = [astroplan.AtNightConstraint.twilight_nautical()]
        else:
            raise ValueError("Unknown twilight type.")

        # calculate end time
        end = start + TimeDelta(self._schedule_range * u.hour)

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
                    name=task.name,
                )
            )

        # return all
        return blocks, start, end, constraints

    async def _schedule_blocks(
        self, blocks: list[ObservingBlock], start: Time, end: Time, constraints: list[Any]
    ) -> list[ObservingBlock]:

        # run actual scheduler in separate process and wait for it
        queue_out: mp.Queue[ObservingBlock] = mp.Queue()
        p = mp.Process(target=self._schedule_process, args=(blocks, start, end, constraints, queue_out))
        p.start()

        # wait for process to finish
        # note that the process only finishes, when the queue is empty! so we have to poll the queue first
        # and then the process.
        loop = asyncio.get_running_loop()
        scheduled_blocks: list[ObservingBlock] = await loop.run_in_executor(None, queue_out.get, True)
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


__all__ = ["AstroplanScheduler"]
