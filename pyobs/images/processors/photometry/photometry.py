from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Photometry(ImageProcessor):
    """Base class for photometry processors."""
    __module__ = 'pyobs.images.processors.photometry'

    def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """
        raise NotImplementedError


__all__ = ['Photometry']
