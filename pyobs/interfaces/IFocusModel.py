from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .interface import Interface


@dataclass
class OptimalFocusState:
    focus: float
    time: Time = field(default_factory=Time.now)


class IFocusModel(Interface, metaclass=ABCMeta):
    """The module provides a model for the telescope focus, e.g. based on temperatures."""

    __module__ = "pyobs.interfaces"

    state = OptimalFocusState

    @abstractmethod
    async def set_optimal_focus(self, **kwargs: Any) -> None:
        """Sets optimal focus."""
        ...


__all__ = ["IFocusModel"]
