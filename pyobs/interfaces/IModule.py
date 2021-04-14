from .interface import *


class IModule(Interface):
    __module__ = 'pyobs.interfaces'

    def label(self, *args, **kwargs) -> str:
        """Returns label of module."""
        raise NotImplementedError


__all__ = ['IModule']
