from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class SourceDetection(ImageProcessor):
    """Base class for source detection."""
    __module__ = 'pyobs.images.processors.detection'

    def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """
        raise NotImplementedError


__all__ = ['SourceDetection']
