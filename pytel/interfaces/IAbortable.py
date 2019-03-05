from .interface import *


class IAbortable(Interface):
    def abort(self, *args, **kwargs):
        """Abort current actions."""
        raise NotImplementedError


__all__ = ['IAbortable']
