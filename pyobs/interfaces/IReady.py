from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field

from ..utils.time import Time
from .interface import Interface


class IReady(Interface, metaclass=ABCMeta):
    """The module can be in a "not ready" state for science and need to be initialized in some way."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        ready: bool
        time: Time = field(default_factory=Time.now)


__all__ = ["IReady"]
