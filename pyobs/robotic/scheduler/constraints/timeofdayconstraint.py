from __future__ import annotations

from datetime import time as dtime
from typing import TYPE_CHECKING, Any, ClassVar

import astroplan
import numpy as np
from pydantic import Field

from pyobs.utils.serialization import BaseModel
from pyobs.utils.time import Time

from .constraint import Constraint

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class TimeOfDayWindow(BaseModel):
    """Daily window [start, end) in UTC. If start > end, the window wraps around midnight."""

    start: dtime = Field(default=dtime(0, 0))
    end: dtime = Field(default=dtime(0, 0))

    def contains(self, now: dtime) -> bool:
        # start == end means an empty window
        if self.start <= self.end:
            return self.start <= now < self.end
        return now >= self.start or now < self.end


class _AstroplanTimeOfDayConstraint(astroplan.Constraint):  # type: ignore[misc]
    """Astroplan counterpart of TimeOfDayConstraint."""

    def __init__(self, windows: list[TimeOfDayWindow]) -> None:
        self.windows = windows

    def compute_constraint(self, times: Time, observer: Any, targets: Any) -> np.ndarray:
        utc = np.atleast_1d(times.utc.datetime)
        return np.array([any(w.contains(t.time()) for w in self.windows) for t in utc], dtype=bool)


class TimeOfDayConstraint(Constraint):
    """Constraint that is only satisfied within daily time windows (UTC).

    Multiple windows are ORed. Several constraints are ANDed by the scheduler, so use one constraint with several
    windows. Only the start time of a task is checked, not its end."""

    windows: list[TimeOfDayWindow] = Field(default_factory=list)
    req_token: ClassVar[str | None] = "TOD"

    def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
        windows = ",".join(f"{w.start.strftime('%H:%M')}-{w.end.strftime('%H:%M')}" for w in self.windows)
        return {"WINDOWS": (windows, "UTC")}

    def to_astroplan(self) -> astroplan.Constraint:
        return _AstroplanTimeOfDayConstraint(self.windows)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        now = time.utc.datetime.time()
        return any(window.contains(now) for window in self.windows)


__all__ = ["TimeOfDayConstraint", "TimeOfDayWindow"]
