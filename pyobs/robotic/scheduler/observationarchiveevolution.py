from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import uuid4

from pyobs.robotic.observation import ObservationState, ObservationList

if TYPE_CHECKING:
    from pyobs.robotic import ScheduledTask, Task, Observation
    from pyobs.robotic.observationarchive import ObservationArchive


class ObservationArchiveEvolution:
    def __init__(self, obs_archive: ObservationArchive | None = None):
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Task, ObservationList] = {}

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

    async def observations_for_task(self, task: Task) -> ObservationList:
        if task not in self._obs_for_task:
            self._obs_for_task[task] = (
                ObservationList() if self._obs_archive is None else await self._obs_archive.observations_for_task(task)
            )
        return self._obs_for_task[task]


__all__ = ["ObservationArchiveEvolution"]
