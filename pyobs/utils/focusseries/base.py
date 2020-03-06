from pyobs.utils.images import Image


class FocusSeries:
    def reset(self):
        """Reset focus series."""
        raise NotImplementedError

    def analyse_image(self, image: Image):
        """Analyse given image.

        Args:
            image: Image to analyse
        """
        raise NotImplementedError

    def fit_focus(self) -> (float, float):
        """Fit focus from analysed images

        Returns:
            Tuple of new focus and its error
        """
        raise NotImplementedError


__all__ = ['FocusSeries']
