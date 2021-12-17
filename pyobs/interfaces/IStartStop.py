from abc import ABCMeta
from typing import Any

from .IRunning import IRunning


class IStartStop(IRunning, metaclass=ABCMeta):
    """The module can be started and stopped."""
    __module__ = 'pyobs.interfaces'

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        raise NotImplementedError

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        raise NotImplementedError


__all__ = ['IStartStop']
