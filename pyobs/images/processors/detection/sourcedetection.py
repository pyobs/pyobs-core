from abc import ABCMeta, abstractmethod

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class SourceDetection(ImageProcessor, metaclass=ABCMeta):
    """Base class for source detection."""
    __module__ = 'pyobs.images.processors.detection'

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """
        ...


__all__ = ['SourceDetection']
