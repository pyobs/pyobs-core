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
            binning: Binning to apply to image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.sigma = sigma
        self.order = order
        self.mode = mode
        self.cval = cval
        self.truncate = truncate

    async def __call__(self, image: Image) -> Image:
        """Bin an image.

        Args:
            image: Image to bin.

        Returns:
            Binned image.
        """

        # copy image
        img = image.copy()
        if img.data is None:
            log.warning("No data found in image.")
            return image

        # smooth it
        img.data = scipy.ndimage.gaussian_filter(
            img.data, self.sigma, order=self.order, mode=self.mode, cval=self.cval, truncate=self.truncate
        )

        # return result
        return img


__all__ = ["Smooth"]
