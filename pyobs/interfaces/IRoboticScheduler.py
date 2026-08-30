from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .IRobotic import RoboticTask
from .IStartStop import IStartStop


@dataclass
class SchedulerState:
    last_reschedule: Time | None = None
    time: Time = field(default_factory=Time.now)


class IRoboticScheduler(IStartStop, metaclass=ABCMeta):
    """The module plans a schedule of tasks for an IRobotic executor to run (e.g. Scheduler)."""

    __module__ = "pyobs.interfaces"

    state = SchedulerState

    @abstractmethod
    async def get_schedule(self, limit: int = 20, **kwargs: Any) -> list[RoboticTask]:
        """Return the upcoming (pending/in-progress) schedule, most imminent first.

        Args:
            limit: Maximum number of entries to return. The implementation also enforces its
                own hard ceiling regardless of what's requested here, so the full schedule
                never has to go over the wire.

        Returns:
            Up to `limit` scheduled tasks.
        """
        ...


__all__ = ["IRoboticScheduler", "SchedulerState"]
