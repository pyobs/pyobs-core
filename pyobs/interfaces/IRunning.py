from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field

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


__all__ = ["IRunning", "RunningState"]
