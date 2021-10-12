from .interface import *


class IRunning(Interface):
    """The module can be running."""
    __module__ = 'pyobs.interfaces'

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running."""
        raise NotImplementedError


__all__ = ['IRunning']
