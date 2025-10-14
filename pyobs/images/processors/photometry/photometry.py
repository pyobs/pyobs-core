from abc import ABCMeta, abstractmethod

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Photometry(ImageProcessor, metaclass=ABCMeta):
    """Base class for photometry processors."""

    __module__ = "pyobs.images.processors.photometry"

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """
        ...


__all__ = ["Photometry"]
