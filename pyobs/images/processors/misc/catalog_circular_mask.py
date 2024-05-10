import logging
from typing import Any, Tuple

import numpy as np

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image

log = logging.getLogger(__name__)


class CatalogCircularMask(ImageProcessor):
    """Mask catalog for central circle with given radius."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, radius: float, center: Tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Init an image processor that masks out everything except for a central circle.

        Args:
            radius: radius of the central circle in pixels
            center: fits-header keywords defining the pixel coordinates of the center of the circle
        """
        ImageProcessor.__init__(self, **kwargs)

        # init
        self._center = center
        self._radius = radius

    async def __call__(self, image: Image) -> Image:
        """Remove everything outside the given radius from the image.

        Args:
            image: Image to mask.

        Returns:
            Image with masked Catalog.
        """

        center_x, center_y = image.header[self._center[0]], image.header[self._center[1]]

        catalog = image.safe_catalog
        mask = (catalog["x"] - center_x) ** 2 + (catalog["y"] - center_y) ** 2 <= self._radius**2
        image.catalog = catalog[mask]

        return image


__all__ = ["CatalogCircularMask"]
