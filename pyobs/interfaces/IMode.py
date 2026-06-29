from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class ModeState:
    modes: dict[str, str] = field(default_factory=dict)  # group -> current mode
    time: Time = field(default_factory=Time.now)


class IMode(Interface, metaclass=ABCMeta):
    """The module can change modes in a device."""

    __module__ = "pyobs.interfaces"

    state = ModeState

    @dataclass
    class Capabilities:
        modes: dict[str, list[str]] = field(default_factory=dict)  # group -> list of modes

    @abstractmethod
    async def set_mode(self, mode: str, group: int = 0, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.
            group: Group number

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode selector cannot be moved.
        """
        ...


__all__ = ["IMode", "ModeState"]
