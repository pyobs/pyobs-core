from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import astropy.units as u
import numpy as np
from astropy.time import TimeDelta

from pyobs.object import Object
from pyobs.robotic.storage.observationarchive import ObservationArchive
from pyobs.utils.time import Time

from . import DataProvider
from .constraints import Constraint
from .observationarchiveevolution import ObservationArchiveEvolution
from .taskscheduler import TaskScheduler

if TYPE_CHECKING:
    from pyobs.robotic import Observation, Project, Task


log = logging.getLogger(__name__)


class OnDemandScheduler(TaskScheduler):
    """Scheduler based on merits."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        twilight: str = "astronomical",
        observation_archive: ObservationArchive | dict[str, Any] | None = None,
        constraints: list[Constraint] | list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        """Initialize a new scheduler.

        Args:
            twilight: astronomical or nautical
        """
        Object.__init__(self, **kwargs)

        # get obs archive
        self._obs_archive = (
            self.add_child_object(observation_archive, ObservationArchive) if observation_archive is not None else None
        )

        # store
        self._twilight = twilight
        self._abort: asyncio.Event = asyncio.Event()

        # global constraints
        constraints = constraints or []
        self._global_constraints: list[Constraint] = [Constraint.create(self, c) for c in constraints]

    async def schedule(
        self, tasks: list[Task], projects: list[Project], start: Time, end: Time
    ) -> AsyncIterator[Observation]:
        if self._observer is None:
            raise RuntimeError("No observer given.")

        archive = ObservationArchiveEvolution(self._observer, self._obs_archive)
        data = DataProvider(self._observer, archive)
        projects_dict = {project.code: project for project in projects}

        # schedule from start to end
        async for task in self.schedule_in_interval(tasks, projects_dict, start, end, data):
            # evolve archive
            await data.archive.evolve(task)

            # yield to caller
            yield task

    async def abort(self) -> None:
        self._abort.set()

    async def schedule_in_interval(
        self,
        tasks: list[Task],
        projects: dict[str, Project],
        start: Time,
        end: Time,
        data: DataProvider,
        step: float = 300,
    ) -> AsyncIterator[Observation]:
        time = start
        while time < end:
            latest_end = start

            # reset resolved targets for each new time slot
            for task in tasks:
                task.reset_resolved_target()

            # schedule first in this interval, could be one or two
            async for scheduled_task in self.schedule_first_in_interval(tasks, projects, time, end, data):
                # yield it to caller
                yield scheduled_task

                # check end
                if scheduled_task.end > latest_end:
                    latest_end = scheduled_task.end

            if latest_end == start:
                # no task found, try 5 minutes later
                time += TimeDelta(step * u.second)
            else:
                # set new time from scheduled task
                time = latest_end

    async def schedule_first_in_interval(
        self,
        tasks: list[Task],
        projects: dict[str, Project],
        start: Time,
        end: Time,
        data: DataProvider,
        step: float = 300,
    ) -> AsyncIterator[Observation]:
        # find current best task
        task, merit = await self.find_next_best_task(tasks, projects, start, end, data)

        if task is not None and merit is not None:
            # check, whether there is another task within its duration that  will have a higher merit
            better_task, better_time, better_merit = await self.check_for_better_task(
                task, projects, merit, tasks, start, end, data, step=step
            )

            if better_task is not None and better_time is not None and better_merit is not None:
                # can we maybe postpone the better task to run both?
                postpone_time = await self.can_postpone_task(
                    task, projects, better_task, better_merit, start, end, data
                )
                if postpone_time is not None:
                    # yes, we can! schedule both
                    yield self.create_scheduled_task(task, merit, start)
                    yield self.create_scheduled_task(better_task, better_merit, postpone_time)
                else:
                    # just schedule better_task
                    yield self.create_scheduled_task(better_task, better_merit, better_time)

                    # and find other tasks for in between, new end time is better_time
                    async for between_task in self.schedule_in_interval(tasks, projects, start, better_time, data):
                        yield between_task

            else:
                # this seems to be the best task for now, schedule it
                yield self.create_scheduled_task(task, merit, start)

    def create_scheduled_task(self, task: Task, merit: float, time: Time) -> Observation:
        from pyobs.robotic import Observation

        return Observation(
            task=task,
            start=time,
            end=time + TimeDelta(task.estimate_duration(time=time) * u.second),
            priority=merit,
            target=task.target,
        )

    async def evaluate_constraints(self, task: Task, start: Time, end: Time, data: DataProvider) -> bool:
        """Loops all constraints. If any evaluates to False, return False. Otherwise, return True.

        Args:
            task: Task to evaluate.
            start: Start time.
            end: End time.
            data: Data provider.

        Returns:
            True if all constraints evaluate True, False otherwise.
        """
        for constraint in self._global_constraints + task.constraints:
            if not await constraint(start, task, data):
                return False
        return True

    async def evaluate_merits(self, task: Task, start: Time, end: Time, data: DataProvider) -> float:
        """Loop all merits, evaluate them and multiply the results. If any evaluates to 0, abort and return 0.

        Args:
            task: Task to evaluate.
            start: Start time.
            end: End time.
            data: Data provider.

        Returns:
            The final merit for this task.
        """

        # loop merits
        total_merit = 1.0
        for merit in task.merits:
            total_merit *= await merit(start, task, data)

            # if zero, abort and return it
            if total_merit == 0.0:
                return 0.0

        # done
        return total_merit

    async def evaluate_constraints_and_merits(
        self, tasks: list[Task], projects: dict[str, Project], start: Time, end: Time, data: DataProvider
    ) -> list[float]:
        # evaluate all merit functions at given time
        merits: list[float] = []
        for task in tasks:
            # resolve dynamic target — skip task if no valid target found
            if not await task.resolve_target(start, task, data):
                merits.append(0.0)
                continue

            # evaluate constraints
            if await self.evaluate_constraints(task, start, end, data):
                # now we can evaluate the merits
                if len(task.merits) == 0:
                    # no merits? evaluate to 1
                    merit = 1.0

                elif start + TimeDelta(task.estimate_duration(time=start) * u.second) > end:
                    # if task is too long for the given slot, we evaluate its merits to zero
                    merit = 0.0

                else:
                    merit = await self.evaluate_merits(task, start, end, data)

            else:
                # some constraint failed...
                merit = 0.0

            # multiply with priorities
            if task.priority is not None:
                merit *= task.priority
            if task.project in projects:
                project = projects[task.project]
                if project.priority is not None:
                    merit *= project.priority

            # store it
            merits.append(merit)

        return merits

    async def find_next_best_task(
        self, tasks: list[Task], projects: dict[str, Project], start: Time, end: Time, data: DataProvider
    ) -> tuple[Task | None, float]:

        # evaluate all merit functions at given time
        merits = await self.evaluate_constraints_and_merits(tasks, projects, start, end, data)

        # find max one
        idx = np.argmax(merits)
        task = tasks[idx]

        # if merit is zero, return nothing
        return None if merits[idx] == 0.0 else task, merits[idx]

    async def check_for_better_task(
        self,
        task: Task,
        projects: dict[str, Project],
        merit: float,
        tasks: list[Task],
        start: Time,
        end: Time,
        data: DataProvider,
        step: float = 300,
    ) -> tuple[Task | None, Time | None, float | None]:
        t = start + TimeDelta(step * u.second)
        while t < start + TimeDelta(task.estimate_duration(time=start) * u.second):
            merits = await self.evaluate_constraints_and_merits(tasks, projects, t, end, data)
            for i, m in enumerate(merits):
                if m > merit:
                    return tasks[i], t, m
            t += TimeDelta(step * u.second)
        return None, None, None

    async def can_postpone_task(
        self,
        task: Task,
        projects: dict[str, Project],
        better_task: Task,
        better_merit: float,
        start: Time,
        end: Time,
        data: DataProvider,
    ) -> Time | None:
        # new start time of better_task would be after the execution of task
        better_start: Time = start + TimeDelta(task.estimate_duration(time=start) * u.second)

        # evaluate merit of better_task at new start time
        merit = (await self.evaluate_constraints_and_merits([better_task], projects, better_start, end, data))[0]

        # if it got better, return it, otherwise return Nones
        if merit >= better_merit:
            return better_start
        else:
            return None


__all__ = ["OnDemandScheduler"]
