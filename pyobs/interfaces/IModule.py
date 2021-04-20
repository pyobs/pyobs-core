from .interface import *


class IModule(Interface):
    """The module is actually a module. Implemented by all modules."""
    __module__ = 'pyobs.interfaces'

    def label(self, *args, **kwargs) -> str:
        """Returns label of module."""
        raise NotImplementedError


__all__ = ['IModule']
