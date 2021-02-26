from astropy.table import Table

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class SourceDetection(ImageProcessor):
    def __call__(self, image: Image) -> Table:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Full table with results.
        """
        raise NotImplementedError


__all__ = ['SourceDetection']
