import logging
from typing import Tuple, Any

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestStarOffsets(Offsets):
    """Calculates offsets from the center of the image to the brightest star."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, center: Tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        # init
        self._center = center

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        # get catalog and sort by flux
        cat = image.catalog
        if cat is None or len(cat) < 1:
            log.warning("No catalog found in image.")
            return image
        cat.sort("flux", reverse=True)

        # get first X/Y coordinates
        x, y = cat["x"][0], cat["y"][0]

        # get center
        center_x, center_y = image.header[self._center[0]], image.header[self._center[1]]

        # calculate offset
        dx, dy = center_x - x, center_y - y

        # set it and return image
        image.set_meta(PixelOffsets(dx, dy))
        return image


__all__ = ["BrightestStarOffsets"]
