from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class GainState:
    gain: float
    offset: float
    time: Time = field(default_factory=Time.now)


class IGain(Interface, metaclass=ABCMeta):
    """The camera supports setting of gain, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    state = GainState

    @abstractmethod
    async def set_gain(self, gain: float, **kwargs: Any) -> None:
        """Set the camera gain.

        Args:
            gain: New camera gain.

        Raises:
            ValueError: If gain could not be set.
        """
        ...

    @abstractmethod
    async def set_offset(self, offset: float, **kwargs: Any) -> None:
        """Set the camera offset.

        Args:
            offset: New camera offset.

        Raises:
            ValueError: If offset could not be set.
        """
        ...


__all__ = ["IGain", "GainState"]
