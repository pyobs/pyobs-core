from abc import ABCMeta
from typing import Any

from .IAbortable import IAbortable


class IRunnable(IAbortable, metaclass=ABCMeta):
    """The module has some action that can be started remotely."""
    __module__ = 'pyobs.interfaces'

    async def run(self, **kwargs: Any) -> None:
        """Perform module task"""
        raise NotImplementedError


__all__ = ['IRunnable']
