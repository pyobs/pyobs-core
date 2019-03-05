from .interface import *


class IAutoFocus(Interface):
    def auto_focus(self, count: int, step: float, guess: float, exposure_time: int, *args, **kwargs) -> float:
        """Perform an auto-focus series.

        This method performs an auto-focus series with "count" images on each side of the initial guess and the given
        step size. With count=3, step=1 and guess=10, this takes images at the following focus values:
            7, 8, 9, 10, 11, 12, 13

        Args:
            count: Number of images to take on each side of the initial guess. Should be an odd number.
            step: Step size.
            guess: Initial guess.
            exposure_time: Exposure time for images.

        Returns:
            Obtained best focus model.

        Raises:
            ValueError: If focus could not be obtained.
        """
        raise NotImplementedError


__all__ = ['IAutoFocus']
