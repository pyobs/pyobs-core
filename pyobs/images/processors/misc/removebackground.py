import logging
from typing import Any, Tuple
from astropy.stats import SigmaClip

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image

log = logging.getLogger(__name__)


class RemoveBackground(ImageProcessor):
    """Remove background from image."""
    __module__ = 'pyobs.images.processors.misc'

    def __init__(self, sigma: float = 3., box_size: Tuple[int, int] = (50, 50), filter_size: Tuple[int, int] = (3, 3),
                 **kwargs: Any):
        """Init an image processor that removes background from image.

        Args:
            sigma: Sigma for clipping
            box_size: Box size for bkg estimation.
            filter_size: Size of filter.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.sigma = sigma
        self.box_size = box_size
        self.filter_size = filter_size

    async def __call__(self, image: Image) -> Image:
        """Remove background from image.

        Args:
            image: Image to remove background from.

        Returns:
            Image without background.
        """
        from photutils.background import Background2D, MedianBackground

        # init objects
        sigma_clip = SigmaClip(sigma=self.sigma)
        bkg_estimator = MedianBackground()

        # calculate background
        bkg = Background2D(image.data, self.box_size, filter_size=self.filter_size,
                           sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)

        # copy image and remove background
        img = image.copy()
        img.data = img.data - bkg.background
        return img


__all__ = ['RemoveBackground']
