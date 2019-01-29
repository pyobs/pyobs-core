from .interface import *


class ICameraWindow(Interface):
    def get_full_frame(self, *args, **kwargs) -> dict:
        """Returns full size of CCD."""
        raise NotImplementedError

    def set_window(self, left: float, top: float, width: float, height: float, *args, **kwargs) -> bool:
        """set the camera window"""
        raise NotImplementedError

    def get_window(self, *args, **kwargs) -> dict:
        """returns the camera window"""
        raise NotImplementedError


__all__ = ['ICameraWindow']
