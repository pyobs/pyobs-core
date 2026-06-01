from __future__ import annotations
import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4
from astroplan import Observer

from ...utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Observation, Task
    from pyobs.robotic.observationarchive import ObservationArchive
    from pyobs.robotic.observation import ObservationList


class ObservationArchiveEvolution:
    def __init__(self, observer: Observer, obs_archive: ObservationArchive | None = None):
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Any, ObservationList] = {}
        self._obs_for_night: dict[datetime.date, ObservationList] = {}
        self._observer = observer

    async def evolve(self, scheduled_task: Observation) -> None:
        from pyobs.robotic.observation import ObservationState, Observation

        obs = Observation(
            id=str(uuid4()),
            task=scheduled_task.task,
            start=scheduled_task.start,
            end=scheduled_task.end,
            state=ObservationState.COMPLETED,
        )

        await self.observations_for_task(scheduled_task.task)
        self._obs_for_task[scheduled_task.task.id].append(obs)

        night = Time.now().night_obs(self._observer)
        await self.observations_for_night(night)
        self._obs_for_night[night].append(obs)

    async def observations_for_task(self, task: Task) -> ObservationList:
        from pyobs.robotic.observation import ObservationState, ObservationList

        if task.id not in self._obs_for_task:
            if self._obs_archive is not None:
                self._obs_for_task[task.id] = await self._obs_archive.get_observations(
                    task=task, state=ObservationState.COMPLETED
                )
            else:
                self._obs_for_task[task.id] = ObservationList()
        return self._obs_for_task[task.id]

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        from pyobs.robotic.observation import ObservationState, ObservationList

        if date not in self._obs_for_night:
            if self._obs_archive is not None:
                start = Time(datetime.datetime.combine(date, datetime.time(0, 0, 0)))
                end = Time(datetime.datetime.combine(date, datetime.time(23, 59, 59)))
                self._obs_for_night[date] = await self._obs_archive.get_observations(
                    end_after=start, start_before=end, state=ObservationState.COMPLETED
                )
            else:
                self._obs_for_night[date] = ObservationList()
        return self._obs_for_night[date]


__all__ = ["ObservationArchiveEvolution"]
