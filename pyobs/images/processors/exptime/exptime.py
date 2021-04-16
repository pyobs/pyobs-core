import logging

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class ExpTimeEstimator(ImageProcessor):
    """Estimate exposure time."""
    __module__ = 'pyobs.images.processors.exptime'

    def __call__(self, image: Image) -> float:
        """Processes an image and returns a new best exposure time in seconds.

        Args:
            image: Image to process.

        Returns:
            New best exposure time in seconds.
        """
        raise NotImplementedError


__all__ = ['ExpTimeEstimator']
