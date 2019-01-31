from .interface import *


class ICameraWindow(Interface):
    def get_full_frame(self, *args, **kwargs) -> dict:
        """Returns full size of CCD.

        Returns:
            Dictionary with left, top, width, and height set.
        """
        raise NotImplementedError

    def set_window(self, left: float, top: float, width: float, height: float, *args, **kwargs) -> bool:
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Returns:
            Success or not.
        """
        raise NotImplementedError

    def get_window(self, *args, **kwargs) -> dict:
        """Returns the camera window.

        Returns:
            Dictionary with left, top, width, and height set.
        """
        raise NotImplementedError


__all__ = ['ICameraWindow']
