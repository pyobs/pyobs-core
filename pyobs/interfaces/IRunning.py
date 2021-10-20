from typing import Any

from .interface import Interface


class IRunning(Interface):
    """The module can be running."""
    __module__ = 'pyobs.interfaces'

    def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        raise NotImplementedError


__all__ = ['IRunning']
