from .IAbortable import IAbortable


class IRunnable(IAbortable):
    """The module has some action that can be started remotely."""
    __module__ = 'pyobs.interfaces'

    def run(self, *args, **kwargs):
        """Perform module task"""
        raise NotImplementedError


__all__ = ['IRunnable']
