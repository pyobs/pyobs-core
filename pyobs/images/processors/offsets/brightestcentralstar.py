import logging
from typing import Tuple, Any

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestCentralStarOffsets(Offsets):
    """Calculates offsets from the center of the image to the brightest star within a given radius around the center."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(
        self,
        radius: float = None,
        use_arcsec: bool = False,
        center: Tuple[str, str] = ("CRPIX1", "CRPIX2"),
        **kwargs: Any
    ):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        # init
        self._center = center
        self._radius = radius
        self._use_arcsec = use_arcsec

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
        cat = image.safe_catalog
        if cat is None or len(cat) < 1:
            log.warning("No catalog found in image.")
            return image

        # get pixels to acquire on
        center_x, center_y = image.header[self._center[0]], image.header[self._center[1]]

        # transform radius from arcseconds to pixels
        if self._radius is not None:
            if self._use_arcsec:
                # TODO: get platescale from WCS instead of header
                pix_mm = image.header["DET-PIXL"]
                focal_length = image.header["TEL-FOCL"]
                pix_arcsec = pix_mm / focal_length * 180 / np.pi * 3600
                radius = self._radius / pix_arcsec
            else:
                radius = self._radius

            # create circular mask around centre
            circ_mask = (cat["x"] - center_x) ** 2 + (cat["y"] - center_y) ** 2 <= radius**2

            # mask out everything except for central circle
            cat_c = cat[circ_mask]
            cat_c.sort("flux", reverse=True)

            # get first X/Y coordinates
            x, y = cat_c["x"][0], cat_c["y"][0]

        else:
            cat.sort("flux", reverse=True)

            # get first X/Y coordinates
            x, y = cat["x"][0], cat["y"][0]

        # calculate offset
        dx, dy = x - center_x, y - center_y

        # get distance on sky
        wcs = WCS(image.header)
        coords1 = wcs.pixel_to_world(center_x, center_y)
        coords2 = wcs.pixel_to_world(center_x + dx, center_y + dy)

        # set it and return image
        image.set_meta(PixelOffsets(dx, dy))
        image.set_meta(OnSkyDistance(coords1.separation(coords2)))
        return image


__all__ = ["BrightestCentralStarOffsets"]
