from .interface import *


class IDome(Interface):
    def is_observable(self, ra: float, dec: float, *args, **kwargs) -> bool:
        """whether and for long an object at the given coordinates is visible"""
        raise NotImplementedError


__all__ = ['IDome']
