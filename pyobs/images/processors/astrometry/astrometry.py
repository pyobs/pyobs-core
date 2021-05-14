from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Astrometry(ImageProcessor):
    """Base class for astrometry processors"""
    __module__ = 'pyobs.images.processors.astrometry'

    def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.

        Args:
            image: Image to analyse.

        Returns:
            Processed image.
        """
        raise NotImplementedError


__all__ = ['Astrometry']
