from .interface import *


class ICameraBinning(Interface):
    def set_binning(self, x: int, y: int, *args, **kwargs):
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        raise NotImplementedError

    def get_binning(self, *args, **kwargs) -> dict:
        """Returns the camera binning.

        Returns:
            Dictionary with x and y.
        """
        raise NotImplementedError


__all__ = ['ICameraBinning']
