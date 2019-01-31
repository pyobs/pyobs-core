from .interface import *


class ICameraBinning(Interface):
    def set_binning(self, x: int, y: int, *args, **kwargs) -> bool:
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Returns:
            Success or not.
        """
        raise NotImplementedError

    def get_binning(self, *args, **kwargs) -> dict:
        """Returns the camera binning.

        Returns:
            Dictionary with x and y.
        """
        raise NotImplementedError


__all__ = ['ICameraBinning']
