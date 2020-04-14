import logging

from pyobs.utils.images import Image


log = logging.getLogger(__name__)


class BaseGuidingOffset:
    def find_pixel_offset(self, image: Image) -> (float, float):
        """Processes an image and return x/y pixel offset to reference.

        Args:
            image: Image to process.

        Returns:
            x/y pixel offset to reference.

        Raises:
            ValueError if offset could not be found.
        """
        raise NotImplementedError

    def set_reference_image(self, image: Image):
        """Set new reference image.

        Args:
            image: New reference image.
        """
        raise NotImplementedError


__all__ = ['BaseGuidingOffset']
