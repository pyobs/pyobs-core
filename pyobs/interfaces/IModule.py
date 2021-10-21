from typing import Any, Optional

from .interface import Interface


class IModule(Interface):
    """The module is actually a module. Implemented by all modules."""
    __module__ = 'pyobs.interfaces'

    def label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        raise NotImplementedError


__all__ = ['IModule']
