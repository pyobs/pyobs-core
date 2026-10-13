from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from astroplan import Observer

from ...utils.time import Time
from .observingperiod import ObservingMode, ObservingPeriods

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pyobs.robotic import Observation, Task
    from pyobs.robotic.observation import ObservationList
    from pyobs.robotic.storage.observationarchive import ObservationArchive


class ObservationArchiveEvolution:
    def __init__(
        self, observer: Observer, obs_archive: ObservationArchive | None = None, *, mode: ObservingMode = "night"
    ):
        self.periods = ObservingPeriods(observer, mode)
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Any, ObservationList] = {}
        self._obs_for_night: dict[datetime.date, ObservationList] = {}
        self._observer = observer
        self._current_night: datetime.date | None = None
        self._frozen = False

    async def prefetch(self, tasks: Iterable[Task], start: Time, night: datetime.date) -> None:
        """Populates the task cache and the one real night (anchored to `start`) up front. Call
        once per schedule() run before any evaluation, then freeze(). Runs on the caller's
        event loop (real I/O)."""
        self._current_night = night
        for task in tasks:
            await self.observations_for_task(task)
        await self.observations_for_night(night, time=start)

    def freeze(self) -> None:
        """Freezes observation cache. After this: a task-id miss raises RuntimeError; a night
        miss seeds an empty list (future nights are provably empty of COMPLETED observations,
        since `start` is pinned at least `_safety_time` ahead of real wall-clock time)."""
        self._frozen = True

    async def evolve(self, scheduled_task: Observation, night: datetime.date) -> None:
        from pyobs.robotic.observation import Observation, ObservationState

        if self.periods.key(scheduled_task.start) != night:
            raise ValueError("Evolved observation does not match its observing period key.")

        obs = Observation(
            id=str(uuid4()),
            task=scheduled_task.task,
            start=scheduled_task.start,
            end=scheduled_task.end,
            state=ObservationState.COMPLETED,
        )

        await self.observations_for_task(scheduled_task.task)
        self._obs_for_task[scheduled_task.task.id].append(obs)

        # The same reset cycle owns real and simulated history, including future periods.
        await self.observations_for_night(night, time=scheduled_task.start)
        self._obs_for_night[night].append(obs)

    async def observations_for_task(self, task: Task) -> ObservationList:
        from pyobs.robotic.observation import ObservationList, ObservationState

        if task.id not in self._obs_for_task:
            if self._frozen:
                raise RuntimeError(
                    f"Task {task.id} not in observation cache after freeze(). "
                    f"This is a bug -- all task IDs must be prefetched before freeze().",
                )
            if self._obs_archive is not None:
                self._obs_for_task[task.id] = await self._obs_archive.get_observations(
                    task=task, state=ObservationState.COMPLETED
                )
            else:
                self._obs_for_task[task.id] = ObservationList()
        return self._obs_for_task[task.id]

    async def observations_for_night(self, date: datetime.date, *, time: Time | None = None) -> ObservationList:
        """Completed observations starting in the selected half-open history cycle.

        ``date`` is the UTC date of the opening sunrise (night mode) or sunset (day mode).
        ``time`` anchors standalone/lazy calls; date-only calls require a unique reset event.
        Cached reads and frozen future-cycle seeding never perform archive I/O.
        """
        from pyobs.robotic.observation import ObservationList, ObservationState

        if date not in self._obs_for_night:
            if self._frozen:
                # `start` is pinned at least `_safety_time` ahead of real wall-clock time, so any
                # night after the prefetched one cannot possibly have COMPLETED observations yet.
                assert (
                    self._current_night is not None and date > self._current_night
                ), f"Night {date} not prefetched and not strictly after current night {self._current_night}."
                self._obs_for_night[date] = ObservationList()
            elif self._obs_archive is not None:
                start, end = self.periods.bounds(date, time)
                observations = await self._obs_archive.get_observations(
                    start_after=start, start_before=end, state=ObservationState.COMPLETED
                )
                self._obs_for_night[date] = ObservationList([obs for obs in observations if start <= obs.start < end])
            else:
                self._obs_for_night[date] = ObservationList()
        return self._obs_for_night[date]


__all__ = ["ObservationArchiveEvolution"]
