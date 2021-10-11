import logging

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class ExpTimeEstimator(ImageProcessor):
    """Estimate exposure time."""
    __module__ = 'pyobs.images.processors.exptime'

    def __init__(self, *args, **kwargs):
        """Init new exposure time estimator."""
        ImageProcessor.__init__(self, *args, **kwargs)
        self.exp_time = None

    def __call__(self, image: Image) -> Image:
        """Processes an image and stores new exposure time in exp_time attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.
        """
        raise NotImplementedError


__all__ = ['ExpTimeEstimator']
