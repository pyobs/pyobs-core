from .interface import *


class IAbortable(Interface):
    """The module has an abortable action."""
    __module__ = 'pyobs.interfaces'

    def abort(self, *args, **kwargs):
        """Abort current actions."""
        raise NotImplementedError


__all__ = ['IAbortable']
