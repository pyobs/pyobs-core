from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field

from ..utils.time import Time
from .interface import Interface


@dataclass
class ReadyState:
    ready: bool
    time: Time = field(default_factory=Time.now)


class IReady(Interface, metaclass=ABCMeta):
    """The module can be in a "not ready" state for science and need to be initialized in some way."""

    __module__ = "pyobs.interfaces"

    state = ReadyState


__all__ = ["IReady", "ReadyState"]
