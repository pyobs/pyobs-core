from abc import ABCMeta
from typing import Any

from .interface import Interface


class IFocusModel(Interface, metaclass=ABCMeta):
    """The module provides a model for the telescope focus, e.g. based on temperatures."""
    __module__ = 'pyobs.interfaces'

    async def get_optimal_focus(self, **kwargs: Any) -> float:
        """Returns the optimal focus."""
        raise NotImplementedError

    async def set_optimal_focus(self, **kwargs: Any) -> None:
        """Sets optimal focus."""
        raise NotImplementedError


__all__ = ['IFocusModel']
