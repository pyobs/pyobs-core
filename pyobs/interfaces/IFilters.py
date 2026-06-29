from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .IMotion import IMotion


class IFilters(IMotion, metaclass=ABCMeta):
    """The module can change filters in a device."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        filter: str
        time: Time = field(default_factory=Time.now)

    @dataclass
    class Capabilities:
        filters: list[str] = field(default_factory=list)

    @abstractmethod
    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If an invalid filter was given.
            MoveError: If filter wheel cannot be moved.
        """
        ...


__all__ = ["IFilters"]
