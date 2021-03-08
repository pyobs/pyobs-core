from astropy.table import Table

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Photometry(ImageProcessor):
    def __call__(self, image: Image) -> Table:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Full table with results.
        """
        raise NotImplementedError


__all__ = ['Photometry']