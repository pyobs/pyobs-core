import logging
from typing import Tuple

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class Offsets(ImageProcessor):
    """Base class for determining offsets."""
    __module__ = 'pyobs.images.processors.offsets'

    def reset(self):
        """Resets guiding."""
        raise NotImplementedError

    def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """
        raise NotImplementedError


__all__ = ['Offsets']
