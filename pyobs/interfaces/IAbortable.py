from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IAbortable(Interface, metaclass=ABCMeta):
    """The module has an abortable action."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        ...


__all__ = ["IAbortable"]
