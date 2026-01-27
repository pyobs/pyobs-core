from __future__ import annotations
import abc
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from pyobs.object import Object
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task, Observation

log = logging.getLogger(__name__)


class TaskScheduler(Object, metaclass=abc.ABCMeta):
    """Abstract base class for tasks scheduler."""

    @abc.abstractmethod
    async def schedule(self, tasks: list[Task], start: Time, end: Time) -> AsyncIterator[Observation]:
        # if we don't yield once here, mypy doesn't like this, see:
        # https://github.com/python/mypy/issues/5385
        # https://github.com/python/mypy/issues/5070
        yield Observation(tasks[0], start, end)

    @abc.abstractmethod
    async def abort(self) -> None: ...


__all__ = ["TaskScheduler"]
