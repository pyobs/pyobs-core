import logging

from pyobs.images import Image
from ._photutil_aperture_photometry import _PhotUtilAperturePhotometry
from .photometry import Photometry

log = logging.getLogger(__name__)


class PhotUtilsPhotometry(Photometry):
    """Perform photometry using PhotUtils."""

    __module__ = "pyobs.images.processors.photometry"

    def __init__(self, **kwargs):
        """Initializes an aperture photometry based on PhotUtils.

        Args:
            threshold: Threshold pixel value for detection.
            minarea: Minimum number of pixels required for detection.
            deblend_nthresh: Number of thresholds used for object deblending.
            deblend_cont: Minimum contrast ratio used for object deblending.
            clean: Perform cleaning?
            clean_param: Cleaning parameter (see SExtractor manual).
            *args:
            **kwargs:
        """
        Photometry.__init__(self, **kwargs)

    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """

        if image.pixel_scale is None:
            log.warning("No pixel scale provided by image.")
            return image

        if image.catalog is None:
            log.warning("No catalog in image.")
            return image

        positions = [(x - 1, y - 1) for x, y in image.catalog.iterrows("x", "y")]

        photometry = _PhotUtilAperturePhotometry(image, positions)

        for diameter in range(1, 9):
            await photometry(diameter)

        output_image = image.copy()
        output_image.catalog = photometry.catalog
        return output_image


__all__ = ["PhotUtilsPhotometry"]
