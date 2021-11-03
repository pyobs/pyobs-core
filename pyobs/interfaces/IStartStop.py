from typing import Any

from .IRunning import IRunning


class IStartStop(IRunning):
    """The module can be started and stopped."""
    __module__ = 'pyobs.interfaces'

    def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        raise NotImplementedError

    def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        raise NotImplementedError


__all__ = ['IStartStop']
