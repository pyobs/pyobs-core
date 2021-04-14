from .IAbortable import IAbortable


class IRunnable(IAbortable):
    __module__ = 'pyobs.interfaces'

    def run(self, *args, **kwargs):
        """Perform module task"""
        raise NotImplementedError


__all__ = ['IRunnable']
