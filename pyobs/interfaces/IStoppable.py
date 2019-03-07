from .interface import *


class IStoppable(Interface):
    def start(self, *args, **kwargs):
        """Starts a service."""
        raise NotImplementedError

    def stop(self, *args, **kwargs):
        """Stops a service."""
        raise NotImplementedError

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running."""
        raise NotImplementedError


__all__ = ['IStoppable']
