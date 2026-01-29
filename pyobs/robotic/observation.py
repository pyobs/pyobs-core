from __future__ import annotations

from collections import UserList
from enum import Enum
from typing import TYPE_CHECKING, Any
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import Task


class ObservationState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    ABORTED = "aborted"
    CANCELED = "canceled"
    FAILED = "failed"


class Observation:
    """A scheduled task."""

    def __init__(
        self, task: Task, start: Time, end: Time, id: Any = None, state: ObservationState = ObservationState.PENDING
    ):
        self._task = task
        self._start = start
        self._end = end
        self._id = id
        self._state = state

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Observation:
        from .task import Task

        return Observation(
            task=Task.from_dict(data["task"]),
            start=Time(data["start"]),
            end=Time(data["end"]),
            id=data["id"],
            state=ObservationState(data["state"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(
            task=self.task.to_dict(),
            start=self._start.isot,
            end=self._end.isot,
            id=self._id,
            state=self._state.value,
        )

    def __str__(self) -> str:
        return (
            f"Observation {self._id} of {self.task.name} (#{self.task.id}) "
            f"from {self.start} to {self.end} [{self.state.value}]"
        )

    @property
    def id(self) -> Any:
        """Returns the id."""
        return self._id

    @property
    def task(self) -> Task:
        """Returns the task."""
        return self._task

    @property
    def start(self) -> Time:
        """Start time for task"""
        return self._start

    @property
    def end(self) -> Time:
        """End time for task"""
        return self._end

    @property
    def state(self) -> ObservationState:
        """Observation state"""
        return self._state

    @state.setter
    def state(self, value: ObservationState) -> None:
        """Sets the state of the task."""
        self._state = value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return self.task.id == other.task.id and self.start == other.start and self.end == other.end
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Observation):
            return self.task.id != other.task.id or self.start != other.start or self.end != other.end
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
