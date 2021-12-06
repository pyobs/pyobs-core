from typing import Any

from .interface import Interface


class IAbortable(Interface):
    """The module has an abortable action."""
    __module__ = 'pyobs.interfaces'

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        raise NotImplementedError


__all__ = ['IAbortable']
