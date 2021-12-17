from abc import ABCMeta, abstractmethod
from typing import Any

from .IRunning import IRunning


class IStartStop(IRunning, metaclass=ABCMeta):
    """The module can be started and stopped."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        ...

    @abstractmethod
    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        ...


__all__ = ['IStartStop']
