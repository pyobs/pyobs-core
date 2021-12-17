from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IFocusModel(Interface, metaclass=ABCMeta):
    """The module provides a model for the telescope focus, e.g. based on temperatures."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def get_optimal_focus(self, **kwargs: Any) -> float:
        """Returns the optimal focus."""
        ...

    @abstractmethod
    async def set_optimal_focus(self, **kwargs: Any) -> None:
        """Sets optimal focus."""
        ...


__all__ = ['IFocusModel']
