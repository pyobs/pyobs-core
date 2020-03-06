from .IAbortable import IAbortable


class IRunnable(IAbortable):
    def run(self, *args, **kwargs):
        """Perform module task"""
        raise NotImplementedError


__all__ = ['IRunnable']
