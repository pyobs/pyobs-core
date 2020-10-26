from .interface import *


class IModule(Interface):
    def label(self, *args, **kwargs) -> str:
        """Returns label of module."""
        raise NotImplementedError


__all__ = ['IModule']
