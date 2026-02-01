from __future__ import annotations

from collections import UserList
from enum import Enum
from typing import Any
from pydantic import BaseModel
from astropydantic import AstroPydanticTime  # type: ignore

from pyobs.utils.time import Time


class ObservationState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    ABORTED = "aborted"
    CANCELED = "canceled"
    FAILED = "failed"


class Observation(BaseModel):
    id: Any
    task_id: Any
    start: AstroPydanticTime
    end: AstroPydanticTime
    state: ObservationState


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
            new_list = [obs for obs in new_list if obs.task_id == task_id]
        if after is not None:
            new_list = [obs for obs in new_list if obs.start >= after]
        return ObservationList(new_list)


__all__ = ["Observation", "ObservationState", "ObservationList"]
