from .IRunning import IRunning


class IStoppable(IRunning):
    """The module can be started and stopped."""
    __module__ = 'pyobs.interfaces'

    def start(self, *args, **kwargs):
        """Starts a service."""
        raise NotImplementedError

    def stop(self, *args, **kwargs):
        """Stops a service."""
        raise NotImplementedError


__all__ = ['IStoppable']
