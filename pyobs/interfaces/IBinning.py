from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


class IBinning(Interface, metaclass=ABCMeta):
    """The camera supports binning, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        x: int
        y: int
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        ...

    @abstractmethod
    async def list_binnings(self, **kwargs: Any) -> list[IBinning.State]:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """
        ...


__all__ = ["IBinning"]
