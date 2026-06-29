from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class RunningState:
    running: bool
    time: Time = field(default_factory=Time.now)


class IRunning(Interface, metaclass=ABCMeta):
    """The module can be running."""

    __module__ = "pyobs.interfaces"

    state = RunningState

    @abstractmethod
    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        ...


__all__ = ["IRunning", "RunningState"]
