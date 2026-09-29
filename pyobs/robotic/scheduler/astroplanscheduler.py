from __future__ import annotations

import asyncio
import logging
import multiprocessing as mp
import queue
import traceback
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import astroplan
import astropy.units as u
from astroplan import FixedTarget, ObservingBlock
from astropy.time import Time as AstropyTime

from pyobs.object import Object
from pyobs.robotic.instruments import InstrumentCapabilities
from pyobs.utils.time import Time

from .targets import SiderealTarget
from .taskscheduler import TaskScheduler

if TYPE_CHECKING:
    from pyobs.robotic import Observation, ObservationList, Project, Task

log = logging.getLogger(__name__)

# (task id, start, end) of a scheduled block, as sent back from the scheduler process
ScheduledBlock = tuple[Any, AstropyTime, AstropyTime]


class AstroplanScheduler(TaskScheduler):
    """Scheduler based on astroplan."""

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

    async def schedule(
        self,
        tasks: list[Task],
        projects: list[Project],
        start: Time,
        end: Time,
        instrument_capabilities: InstrumentCapabilities | None = None,
    ) -> AsyncIterator[Observation]:
        # instrument_capabilities: accepted for TaskScheduler interface consistency, unused --
        # this scheduler reads the stored Task.duration field rather than calling
        # estimate_duration() live (see specs/plans/2026-09-01-instrument-capability-duration-estimates.md
        # Non-goals).
        # is lock acquired? send abort signal
        if self._lock.locked():
            await self.abort()

        # get lock
        async with self._lock:
            # clear abort event for this run
            self._abort.clear()
            # prepare scheduler
            blocks, start, end, constraints = await self._prepare_schedule(tasks, start, end)

            # schedule
            if not blocks:
                return
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
        from pyobs.robotic.scheduler.dataprovider import DataProvider

        data = DataProvider(self.observer)

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
            # resolve dynamic target
            if not await task.resolve_target(start, task, data):
                log.warning("Could not resolve target for task '%s', skipping.", task.name)
                continue

            target = task.target
            if not isinstance(target, SiderealTarget):
                log.warning("Non-sidereal targets not supported.")
                continue

            priority = (1000.0 - task.priority) if task.priority is not None else 1000.0
            if priority < 0:
                priority = 0

            blocks.append(
                ObservingBlock(
                    FixedTarget(target.coord, name=target.name),
                    task.duration * u.second,
                    priority,
                    constraints=[c.to_astroplan() for c in task.constraints] if task.constraints else None,
                    # no task in configuration: scheduled blocks are pickled back from the worker process,
                    # and tasks reference unpicklable comm proxies; _convert_blocks matches by name instead
                    name=task.id,
                )
            )

        # return all
        return blocks, start, end, constraints

    async def _schedule_blocks(
        self, blocks: list[ObservingBlock], start: Time, end: Time, constraints: list[Any], abort: asyncio.Event
    ) -> list[ScheduledBlock]:

        # run actual scheduler in separate process and wait for it
        queue_out: mp.Queue[tuple[str, Any]] = mp.Queue()
        p = mp.Process(target=self._schedule_process, args=(blocks, start, end, constraints, self.observer, queue_out))
        p.start()

        # wait for result, polling the queue: the process only finishes when the queue is drained, and a
        # blocking get() would hang forever if the process dies without sending anything
        while True:
            if abort.is_set():
                p.kill()
                return []
            try:
                status, result = queue_out.get_nowait()
                break
            except queue.Empty:
                pass
            if not p.is_alive():
                # anything put before exit has been flushed to the pipe by now
                try:
                    status, result = queue_out.get_nowait()
                    break
                except queue.Empty:
                    raise RuntimeError(f"Scheduler process exited with code {p.exitcode} without sending a result.")
            await asyncio.sleep(0.1)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, p.join)

        if status == "error":
            raise RuntimeError(f"Scheduler process failed:\n{result}")
        scheduled_blocks: list[ScheduledBlock] = result
        return scheduled_blocks

    @staticmethod
    def _schedule_process(
        blocks: list[ObservingBlock],
        start: Time,
        end: Time,
        constraints: list[Any],
        observer: Any,
        queue_out: mp.Queue[tuple[str, Any]],
    ) -> None:
        """Actually do the scheduling, usually run in a separate process.

        Only plain (name, start, end) tuples are sent back, since the result is pickled and blocks may
        reference objects that can't be pickled.
        """

        # log it
        log.info("Calculating schedule for %d schedulable block(s) starting at %s...", len(blocks), start)

        try:
            # we don't need any transitions
            transitioner = astroplan.Transitioner()

            # create scheduler
            scheduler = astroplan.PriorityScheduler(constraints, observer, transitioner=transitioner)

            # run scheduler
            logging.disable(logging.WARNING)
            try:
                time_range = astroplan.Schedule(start, end)
                schedule = scheduler(blocks, time_range)
            finally:
                logging.disable(logging.NOTSET)

            # put scheduled blocks in queue
            queue_out.put(("ok", [(b.name, b.start_time, b.end_time) for b in schedule.scheduled_blocks]))

        except Exception:
            queue_out.put(("error", traceback.format_exc()))

    async def _convert_blocks(self, blocks: list[ScheduledBlock], tasks: list[Task]) -> ObservationList:
        from pyobs.robotic import Observation, ObservationList

        scheduled_tasks = ObservationList()
        for task_id, block_start, block_end in blocks:
            # find task
            for task in tasks:
                if task.id == task_id:
                    break
            else:
                raise ValueError(f"Could not find task with id '{task_id}'")

            # create scheduled task
            scheduled_tasks.append(Observation(task=task, start=block_start, end=block_end, target=task.target))

        return scheduled_tasks


__all__ = ["AstroplanScheduler"]
