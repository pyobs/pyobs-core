from abc import ABCMeta, abstractmethod

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


class Astrometry(ImageProcessor, metaclass=ABCMeta):
    """Base class for astrometry processors"""

    __module__ = "pyobs.images.processors.astrometry"

    @abstractmethod
    async def __call__(self, image: Image) -> Image:
        """Finds astrometric solution to a given image.

        Args:
            image: Image to analyse.

        Returns:
            Processed image.
        """


__all__ = ["Astrometry"]
