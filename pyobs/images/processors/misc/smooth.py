import logging
from typing import Any

import scipy.ndimage

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Smooth(ImageProcessor):
    """smooth an image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        sigma: float,
        order: int = 0,
        mode: str = "reflect",
        cval: float = 0.0,
        truncate: float = 4.0,
        **kwargs: Any,
    ):
        """Init a new smoothing pipeline step.

        Args:
            sigma: Standard deviation for Gaussian kernel.
            order: The order of the filter along each axis.
            mode: Determines how the input array is extended when the filter overlaps a border.
            cval: Value to fill past edges of input if mode is ‘constant’.
            truncate: Truncate the filter at this many standard deviations.

        See Also: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html#scipy-ndimage-gaussian-filter
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.sigma = sigma
        self.order = order
        self.mode = mode
        self.cval = cval
        self.truncate = truncate

    async def __call__(self, image: Image) -> Image:
        """Smooth an image.

        Args:
            image: Image to smooth.

        Returns:
            Smoothed image.
        """

        output_image = image.copy()
        if output_image.data is None:
            log.warning("No data found in image.")
            return image

        output_image.data = scipy.ndimage.gaussian_filter(
            output_image.data, self.sigma, order=self.order, mode=self.mode, cval=self.cval, truncate=self.truncate
        )

        return output_image


__all__ = ["Smooth"]
