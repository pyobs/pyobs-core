import asyncio
import copy
import logging
import multiprocessing as mp
from typing import List, Tuple, Any, Optional, cast

import astroplan
import astropy
import astropy.units as u
from astroplan import ObservingBlock, Observer
from astropy.time import TimeDelta

from pyobs.robotic import TaskSchedule, Task
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class _TaskScheduler:
    def __init__(self, schedule: TaskSchedule, observer: Observer, schedule_range: int, safety_time: int, twilight: str) -> None:
        self._schedule = schedule
        self._observer = observer

        self._schedule_range = schedule_range
        self._safety_time = safety_time
        self._twilight = twilight

        self._blocks: List[ObservingBlock] = []

        self._current_task_id: Optional[str] = None
        self._schedule_start: Optional[Time] = None

    def set_current_task_id(self, task_id: str) -> None:
        self._current_task_id = task_id

    def set_schedule_start(self, time: Optional[Time]) -> None:
        self._schedule_start = time

    def set_blocks(self, blocks: List[ObservingBlock]) -> None:
        self._blocks = blocks

    async def schedule_task(self) -> None:
        try:
            # prepare scheduler
            blocks, start, end, constraints = await self._prepare_schedule()

            # schedule
            scheduled_blocks = await self._schedule_blocks(blocks, start, end, constraints)

            # finish schedule
            await self._finish_schedule(scheduled_blocks, start)

        except ValueError as e:
            log.warning(str(e))

    async def _prepare_schedule(self) -> Tuple[List[ObservingBlock], Time, Time, List[Any]]:
        """TaskSchedule blocks."""

        converted_blocks = await self._convert_blocks_to_astroplan()

        start, end = await self._get_time_range()

        blocks = self._filter_blocks(converted_blocks, end)

        # no blocks found?
        if len(blocks) == 0:
            await self._schedule.set_schedule([], start)
            raise ValueError("No blocks left for scheduling.")

        constraints = await self._get_twilight_constraint()

        # return all
        return blocks, start, end, constraints

    async def _get_twilight_constraint(self) -> List[astroplan.Constraint]:
        if self._twilight == "astronomical":
            return [astroplan.AtNightConstraint.twilight_astronomical()]
        elif self._twilight == "nautical":
            return [astroplan.AtNightConstraint.twilight_nautical()]
        else:
            raise ValueError("Unknown twilight type.")

    async def _convert_blocks_to_astroplan(self) -> List[astroplan.ObservingBlock]:
        copied_blocks = [copy.copy(block) for block in self._blocks]

        for block in copied_blocks:
            self._invert_block_priority(block)
            self._tighten_block_time_constraints(block)

        return copied_blocks

    @staticmethod
    def _invert_block_priority(block: astroplan.ObservingBlock) -> None:
        """
        astroplan's PriorityScheduler expects lower priorities to be more important, so calculate
        1000 - priority
        """
        block.priority = max(1000.0 - block.priority, 0.0)

    @staticmethod
    def _tighten_block_time_constraints(block: astroplan.ObservingBlock) -> None:
        """
        astroplan's PriorityScheduler doesn't match the requested observing windows exactly,
        so we make them a little smaller.
        """
        time_constraints = filter(lambda c: isinstance(c, astroplan.TimeConstraint), block.constraints)
        for constraint in time_constraints:
            constraint.min += 30 * u.second
            constraint.max -= 30 * u.second

    async def _get_time_range(self) -> Tuple[astropy.time.Time, astropy.time.Time]:
        # get start time for scheduler
        start = self._schedule_start
        now_plus_safety = Time.now() + self._safety_time * u.second
        if start is None or start < now_plus_safety:
            # if no ETA exists or is in the past, use safety time
            start = now_plus_safety

        if (running_task := await self._get_current_task()) is not None:
            log.info("Found running block that ends at %s.", running_task.end)

            # get block end plus some safety
            block_end = running_task.end + 10.0 * u.second
            if start < block_end:
                start = block_end
                log.info("Start time would be within currently running block, shifting to %s.", cast(Time, start).isot)

        # calculate end time
        end = start + TimeDelta(self._schedule_range * u.hour)

        return start, end

    async def _get_current_task(self) -> Optional[Task]:
        if self._current_task_id is None:
            log.info("No running block found.")
            return None

        log.info("Trying to find running block in current schedule...")
        tasks = await self._schedule.get_schedule()
        if self._current_task_id in tasks:
            return tasks[self._current_task_id]
        else:
            log.info("Running block not found in last schedule.")
            return None

    def _filter_blocks(self, blocks: List[astroplan.ObservingBlock], end: astropy.time.Time) -> List[astroplan.ObservingBlock]:
        blocks_without_current = filter(lambda x: x.configuration["request"]["id"] != self._current_task_id, blocks)
        blocks_in_schedule_range = filter(lambda b: self._is_block_starting_in_schedule(b, end), blocks_without_current)

        return list(blocks_in_schedule_range)

    @staticmethod
    def _is_block_starting_in_schedule(block: astroplan.ObservingBlock, end: astropy.time.Time) -> bool:
        time_constraints = [c for c in block.constraints if isinstance(c, astroplan.TimeConstraint)]

        # does constraint start before the end of the scheduling range?
        before_end = [c for c in time_constraints if c.min < end]

        return len(time_constraints) == 0 or len(before_end) > 0

    async def _schedule_blocks(
        self, blocks: List[ObservingBlock], start: Time, end: Time, constraints: List[Any]
    ) -> List[ObservingBlock]:

        # run actual scheduler in separate process and wait for it
        qout: mp.Queue[List[ObservingBlock]] = mp.Queue()
        p = mp.Process(target=self._schedule_process, args=(blocks, start, end, constraints, qout))
        p.start()

        # wait for process to finish
        # note that the process only finishes, when the queue is empty! so we have to poll the queue first
        # and then the process.
        loop = asyncio.get_running_loop()
        scheduled_blocks: List[ObservingBlock] = await loop.run_in_executor(None, qout.get, True)
        await loop.run_in_executor(None, p.join)
        return scheduled_blocks

    async def _finish_schedule(self, scheduled_blocks: List[ObservingBlock], start: Time) -> None:
        # update
        await self._schedule.set_schedule(scheduled_blocks, start)
        if len(scheduled_blocks) > 0:
            log.info("Finished calculating schedule for %d block(s):", len(scheduled_blocks))
            for i, block in enumerate(scheduled_blocks, 1):
                log.info(
                    "  #%d: %s to %s (%.1f)",
                    block.configuration["request"]["id"],
                    block.start_time.strftime("%H:%M:%S"),
                    block.end_time.strftime("%H:%M:%S"),
                    block.priority,
                )
        else:
            log.info("Finished calculating schedule for 0 blocks.")

    def _schedule_process(
        self,
        blocks: List[ObservingBlock],
        start: Time,
        end: Time,
        constraints: List[Any],
        scheduled_blocks: mp.Queue   # type: ignore
    ) -> None:
        """Actually do the scheduling, usually run in a separate process."""

        # log it
        log.info("Calculating schedule for %d schedulable block(s) starting at %s...", len(blocks), start)

        # we don't need any transitions
        transitioner = astroplan.Transitioner()

        # create scheduler
        scheduler = astroplan.PriorityScheduler(constraints, self._observer, transitioner=transitioner)

        # run scheduler
        time_range = astroplan.Schedule(start, end)
        schedule = scheduler(blocks, time_range)

        # put scheduled blocks in queue
        scheduled_blocks.put(schedule.scheduled_blocks)