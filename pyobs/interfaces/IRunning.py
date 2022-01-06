from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IRunning(Interface, metaclass=ABCMeta):
    """The module can be running."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        ...


__all__ = ["IRunning"]
