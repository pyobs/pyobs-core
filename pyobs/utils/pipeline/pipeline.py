import logging

from pyobs.images import BiasImage, DarkImage, FlatImage, Image


log = logging.getLogger(__name__)


class Pipeline:
    def calibrate(self, image: Image, bias: BiasImage = None, dark: DarkImage = None, flat: FlatImage = None) -> Image:
        """Calibrate a single science frame.

        Args:
            image: Image to calibrate.
            bias: Bias frame to use.
            dark: Dark frame to use.
            flat: Flat frame to use.

        Returns:
            Calibrated image.
        """
        raise NotImplementedError


__all__ = ['Pipeline']
