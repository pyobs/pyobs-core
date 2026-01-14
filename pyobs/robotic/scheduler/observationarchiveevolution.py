from __future__ import annotations
import datetime
from typing import TYPE_CHECKING
from uuid import uuid4
from astroplan import Observer

from pyobs.robotic.observation import ObservationState, ObservationList
from ...utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import ScheduledTask, Task, Observation
    from pyobs.robotic.observationarchive import ObservationArchive


class ObservationArchiveEvolution:
    def __init__(self, observer: Observer, obs_archive: ObservationArchive | None = None):
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Task, ObservationList] = {}
        self._obs_for_night: dict[datetime.date, ObservationList] = {}
        self._observer = observer

    async def evolve(self, scheduled_task: ScheduledTask) -> None:
        obs = Observation(
            id=str(uuid4()),
            task_id=scheduled_task.task.id,
            start=scheduled_task.start,
            end=scheduled_task.end,
            state=ObservationState.COMPLETED,
        )

        await self.observations_for_task(scheduled_task.task)
        self._obs_for_task[scheduled_task.task].append(obs)

        night = Time.now().night_obs(self._observer)
        await self.observations_for_night(night)
        self._obs_for_night[night].append(obs)

    async def observations_for_task(self, task: Task) -> ObservationList:
        if task not in self._obs_for_task:
            self._obs_for_task[task] = (
                ObservationList() if self._obs_archive is None else await self._obs_archive.observations_for_task(task)
            )
        return self._obs_for_task[task]

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        if date not in self._obs_for_night:
            self._obs_for_night[date] = (
                ObservationList() if self._obs_archive is None else await self._obs_archive.observations_for_night(date)
            )
        return self._obs_for_night[date]


__all__ = ["ObservationArchiveEvolution"]
