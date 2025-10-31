from __future__ import annotations
import abc
import logging
from typing import TYPE_CHECKING

from pyobs.object import Object
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task, ScheduledTask

log = logging.getLogger(__name__)


class TaskScheduler(Object, metaclass=abc.ABCMeta):
    """Abstract base class for tasks scheduler."""

    @abc.abstractmethod
    async def schedule(self, tasks: list[Task], start: Time) -> list[ScheduledTask]: ...

    @abc.abstractmethod
    async def abort(self) -> None: ...


__all__ = ["TaskScheduler"]
