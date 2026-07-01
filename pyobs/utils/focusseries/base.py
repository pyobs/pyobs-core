from __future__ import annotations

from pyobs.images import Image
from pyobs.interfaces import AutoFocusPoint


class FocusSeries:
    """Base class for focus series helper classes."""

    __module__ = "pyobs.utils.focusseries"

    def reset(self) -> None:
        """Reset focus series."""
        raise NotImplementedError

    async def analyse_image(self, image: Image, focus_value: float) -> None:
        """Analyse given image.

        Args:
            image: Image to analyse
            focus_value: Value to fit along, e.g. focus value or its offset
        """
        raise NotImplementedError

    def get_data_points(self) -> list[AutoFocusPoint]:
        """Returns a list of data points."""
        ...

    def fit_focus(self) -> tuple[float, float]:
        """Fit focus from analysed images

        Returns:
            Tuple of new focus and its error
        """
        raise NotImplementedError


__all__ = ["FocusSeries"]
