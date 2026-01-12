from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel
from astropydantic import AstroPydanticTime  # type: ignore


class ObservationState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    ABORTED = "aborted"
    CANCELED = "canceled"


class Observation(BaseModel):
    id: Any
    task_id: Any
    start: AstroPydanticTime
    end: AstroPydanticTime
    state: ObservationState


__all__ = ["Observation", "ObservationState"]
