import abc
import logging

from pyobs.object import Object
from pyobs.robotic import Task, ScheduledTask
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class TaskScheduler(Object, metaclass=abc.ABCMeta):
    """Abstract base class for tasks scheduler."""

    @abc.abstractmethod
    async def schedule(self, tasks: list[Task], start: Time) -> list[ScheduledTask]: ...


__all__ = ["TaskScheduler"]
