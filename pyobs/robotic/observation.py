from __future__ import annotations
from collections import UserList
from enum import Enum
from typing import Any
from astropydantic import AstroPydanticTime  # type: ignore
from pydantic import BaseModel

from pyobs.utils.time import Time
from pyobs.robotic.task import Task


class ObservationState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    ABORTED = "aborted"
    CANCELED = "canceled"
    FAILED = "failed"


class Observation(BaseModel):
    """A scheduled task."""

    id: Any = None
    task: Task
    start: AstroPydanticTime
    end: AstroPydanticTime
    state: ObservationState = ObservationState.PENDING

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


class ObservationList(UserList[Observation]):
    def __init__(self, observations: list[Observation] | None = None):
        UserList.__init__(self, observations)

    def filter(
        self, state: ObservationState | None = None, task_id: int | None = None, after: Time | None = None
    ) -> ObservationList:
        new_list = self.data
        if state is not None:
            new_list = [obs for obs in new_list if obs.state == state]
        if task_id is not None:
            new_list = [obs for obs in new_list if obs.task.id == task_id]
        if after is not None:
            new_list = [obs for obs in new_list if obs.start >= after]
        return ObservationList(new_list)


__all__ = ["Observation", "ObservationState", "ObservationList"]
