import logging
from typing import Tuple

from pyobs.images import Image


log = logging.getLogger(__name__)


class BaseGuidingOffset:
    def reset(self):
        """Resets guiding."""
        raise NotImplementedError

    def find_pixel_offset(self, image: Image) -> Tuple[float, float]:
        """Processes an image and return x/y pixel offset to reference.

        Args:
            image: Image to process.

        Returns:
            x/y pixel offset to reference.

        Raises:
            ValueError if offset could not be found.
        """
        raise NotImplementedError


__all__ = ['BaseGuidingOffset']
