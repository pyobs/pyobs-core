from .interface import *


class IAbortable(Interface):
    def abort(self, *args, **kwargs) -> bool:
        """Abort current actions.

        Returns:
            Success.
        """
        raise NotImplementedError


__all__ = ['IAbortable']
