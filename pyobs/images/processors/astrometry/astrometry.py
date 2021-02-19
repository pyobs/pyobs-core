from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Astrometry(ImageProcessor):
    def __call__(self, image: Image):
        """Find astrometric solution on given image.

        Args:
            image: Image to analyse.
        """
        raise NotImplementedError


__all__ = ['Astrometry']
