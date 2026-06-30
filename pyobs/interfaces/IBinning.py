from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class BinningState:
    x: int
    y: int
    time: Time = field(default_factory=Time.now)


@dataclass
class BinningCapabilities:
    binnings: list[BinningState] = field(default_factory=list)


class IBinning(Interface, metaclass=ABCMeta):
    """The camera supports binning, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    state = BinningState
    capabilities = BinningCapabilities

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


__all__ = ["IBinning", "BinningState", "BinningCapabilities"]
