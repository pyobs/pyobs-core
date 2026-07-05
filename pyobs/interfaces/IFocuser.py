from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IMotion import IMotion


@dataclass
class FocuserState:
    focus: Annotated[float, Unit.MM]
    focus_offset: Annotated[float, Unit.MM]
    time: Time = field(default_factory=Time.now)


class IFocuser(IMotion, metaclass=ABCMeta):
    """The module is a focusing device."""

    __module__ = "pyobs.interfaces"

    state = FocuserState

    @abstractmethod
    async def set_focus(self, focus: Annotated[float, Unit.MM], **kwargs: Any) -> None:
        """Sets new focus.

        Args:
            focus: New focus value in mm.

        Raises:
            MoveError: If telescope cannot be moved.
            InterruptedError: If movement was aborted.
        """
        ...

    @abstractmethod
    async def set_focus_offset(self, offset: Annotated[float, Unit.MM], **kwargs: Any) -> None:
        """Sets focus offset.

        Args:
            offset: New focus offset in mm.

        Raises:
            ValueError: If given value is invalid.
            MoveError: If telescope cannot be moved.
        """
        ...


__all__ = ["IFocuser", "FocuserState"]
