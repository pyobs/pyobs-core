from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


class IMultiFiber(Interface, metaclass=ABCMeta):
    """An interface for multi-fiber setups that helps to set/get a fiber and retrieve position and size of the
    current fiber on the acquisition/guiding image."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class Capabilities:
        fiber_count: int = 0
        fiber_names: list[str] = field(default_factory=list)

    @dataclass
    class State:
        fiber: str = ""
        pixel_x: float = 0.0
        pixel_y: float = 0.0
        radius: float = 0.0
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        ...

    @abstractmethod
    async def set_fiber(self, fiber: str, **kwargs: Any) -> None:
        """Sets the currently active fiber. Must be in fiber_names capability.

        Args:
            fiber: Name of fiber to set.
        """
        ...


__all__ = ["IMultiFiber"]
