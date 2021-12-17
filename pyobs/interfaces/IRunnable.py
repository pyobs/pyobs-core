from abc import ABCMeta, abstractmethod
from typing import Any

from .IAbortable import IAbortable


class IRunnable(IAbortable, metaclass=ABCMeta):
    """The module has some action that can be started remotely."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def run(self, **kwargs: Any) -> None:
        """Perform module task"""
        ...


__all__ = ['IRunnable']
