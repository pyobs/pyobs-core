from typing import Tuple

from pyobs.images import Image


class FocusSeries:
    """Base class for focus series helper classes."""
    __module__ = 'pyobs.utils.focusseries'

    def reset(self) -> None:
        """Reset focus series."""
        raise NotImplementedError

    def analyse_image(self, image: Image) -> None:
        """Analyse given image.

        Args:
            image: Image to analyse
        """
        raise NotImplementedError

    def fit_focus(self) -> Tuple[float, float]:
        """Fit focus from analysed images

        Returns:
            Tuple of new focus and its error
        """
        raise NotImplementedError


__all__ = ['FocusSeries']
