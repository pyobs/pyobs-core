import asyncio
import logging
from typing import Any

from pyobs.images import Image
from .photometry import Photometry
from ._sep_aperture_photometry import _SepAperturePhotometry

log = logging.getLogger(__name__)


class SepPhotometry(Photometry):
    """Perform photometry using SEP."""

    __module__ = "pyobs.images.processors.photometry"

    def __init__(self, **kwargs: Any):
        """Initializes a wrapper for SEP. See its documentation for details.

        Highly inspired by LCO's wrapper for SEP, see:
        https://github.com/LCOGT/banzai/blob/master/banzai/photometry.py
        """
        Photometry.__init__(self, **kwargs)

    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._photometry, image)

    def _photometry(self, image: Image) -> Image:
        if image.data is None:
            log.warning("No data found in image.")
            return image

        if image.pixel_scale is None:
            log.warning("No pixel scale provided by image.")
            return image

        if image.catalog is None:
            log.warning("No catalog found in image.")
            return image
        diameters = range(1, 9)

        positions = [(x - 1, y - 1) for x, y in image.catalog.iterrows("x", "y")]
        photometry = _SepAperturePhotometry(image, positions)

        for diameter in diameters:
            photometry(diameter)

        output_image = image.copy()
        output_image.catalog = photometry.catalog
        return output_image


__all__ = ["SepPhotometry"]
