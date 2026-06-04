from __future__ import annotations
from collections import UserList
from enum import StrEnum
from typing import Any, TYPE_CHECKING
from astropydantic import AstroPydanticTime  # type: ignore

from pyobs.object import Object
from pyobs.utils.time import Time
from pyobs.robotic.task import Task
from pyobs.utils.serialization import BaseModel
from pyobs.robotic.scheduler.targets import Target

if TYPE_CHECKING:
    from pyobs.robotic import TaskArchive


class ObservationState(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    ABORTED = "aborted"
    CANCELED = "canceled"
    FAILED = "failed"


class Observation(BaseModel):
    """A scheduled task."""

    id: Any | None = None
    task: Task | Any
    start: AstroPydanticTime
    end: AstroPydanticTime
    state: ObservationState = ObservationState.PENDING
    priority: float | None = None
    target: Target | None = None

    def __str__(self) -> str:
        return (
            f"Observation {self.id} of {self.task.name} (#{self.task.id}) "
            f"from {self.start} to {self.end} [{self.state.value}]"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.task.id == other.task.id and self.start == other.start and self.end == other.end)
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.task.id != other.task.id or self.start != other.start or self.end != other.end)
        return super().__ne__(other)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.start < other.start)
        raise NotImplementedError

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.start > other.start)
        raise NotImplementedError

    def __le__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.start <= other.start)
        raise NotImplementedError

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return bool(self.start >= other.start)
        raise NotImplementedError

    def model_dump(self, use_task_id: bool = False, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        if use_task_id and isinstance(self.task, Task) and self.task.id is not None:
            data["task"] = self.task.id
        if self.target is not None:
            data["target"] = self.target.model_dump()
        return data

    async def fetch_task(self, task_archive: TaskArchive) -> None:
        """Fetch a task from the task archive."""
        if not isinstance(self.task, Task):
            self.task = await task_archive.get_task(self.task)
        # restore resolved target from observation
        if self.task is not None and self.target is not None:
            self.task.set_resolved_target(self.target)


class ObservationList(Userlist[Observation], Object):  # noqa: F821
    def __init__(self, observations: list[Observation] | None = None):
        if observations is None:
            observations = []
        UserList.__init__(self, observations)

    def filter(
        self,
        state: ObservationState | None = None,
        task_id: int | None = None,
        start_before: Time | None = None,
        start_after: Time | None = None,
        end_before: Time | None = None,
        end_after: Time | None = None,
    ) -> ObservationList:
        new_list = self.data
        if state is not None:
            new_list = [obs for obs in new_list if obs.state == state]
        if task_id is not None:
            new_list = [obs for obs in new_list if obs.task.id == task_id]
        if start_before is not None:
            new_list = [obs for obs in new_list if obs.start <= start_before]
        if start_after is not None:
            new_list = [obs for obs in new_list if obs.start >= start_after]
        if end_before is not None:
            new_list = [obs for obs in new_list if obs.end <= end_before]
        if end_after is not None:
            new_list = [obs for obs in new_list if obs.end >= end_after]
        return ObservationList(new_list)

    def model_dump(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [obs.model_dump(**kwargs) for obs in self.data]

    def model_validate(self, data: list[dict[str, Any]], **kwargs: Any) -> ObservationList:
        return ObservationList([self.pyobs_model_validate(Observation, obs, **kwargs) for obs in data])


__all__ = ["Observation", "ObservationState", "ObservationList"]
