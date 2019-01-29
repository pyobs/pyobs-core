from .interface import *


class ICameraBinning(Interface):
    def set_binning(self, x: int, y: int, *args, **kwargs) -> bool:
        """set the camera binning"""
        raise NotImplementedError

    def get_binning(self, *args, **kwargs) -> dict:
        """returns the camera binning"""
        raise NotImplementedError


__all__ = ['ICameraBinning']
