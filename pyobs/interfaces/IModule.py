from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from .interface import Interface


class IModule(Interface, metaclass=ABCMeta):
    """The module is actually a module. Implemented by all modules."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def get_label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        ...

    @abstractmethod
    async def get_version(self, **kwargs: Any) -> str:
        """Returns pyobs version of module."""
        ...


__all__ = ['IModule']
