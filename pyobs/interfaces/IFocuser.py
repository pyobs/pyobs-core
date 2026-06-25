from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .IMotion import IMotion


class IFocuser(IMotion, metaclass=ABCMeta):
    """The module is a focusing device."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        focus: float
        focus_offset: float
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        """Sets new focus.

        Args:
            focus: New focus value.

        Raises:
            MoveError: If telescope cannot be moved.
            InterruptedError: If movement was aborted.
        """
        ...

    @abstractmethod
    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        """Sets focus offset.

        Args:
            offset: New focus offset.

        Raises:
            ValueError: If given value is invalid.
            MoveError: If telescope cannot be moved.
        """
        ...


__all__ = ["IFocuser"]
