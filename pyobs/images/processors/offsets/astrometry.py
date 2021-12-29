import logging
from typing import Any
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from . import Offsets

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class AstrometryOffsets(Offsets):
    """An offset-calculation method based on astrometry. Returns offset to real coordinates."""

    def __init__(self, **kwargs: Any):
        """Initializes new astrometry offsets.

        MUST run after an astrometry processor.
        """
        Offsets.__init__(self, **kwargs)

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        # copy image and get WCS
        # we make our life a little easier by only using the new WCS from astrometry
        img = image.copy()
        wcs = WCS(img.header)

        # get x/y coordinates from CRVAL1/2, i.e. from center with good WCS
        center = SkyCoord(img.header['CRVAL1'] * u.deg, img.header['CRVAL2'] * u.deg, frame='icrs')
        x_center, y_center = wcs.world_to_pixel(center)

        # get x/y coordinates from TEL-RA/-DEC, i.e. from where the telescope thought it's pointing
        tel = SkyCoord(img.header['TEL-RA'] * u.deg, img.header['TEL-DEC'] * u.deg, frame='icrs')
        x_tel, y_tel = wcs.world_to_pixel(tel)

        # calculate offsets as difference between both
        img.set_meta(PixelOffsets(x_tel - x_center, y_tel - y_center))
        img.set_meta(OnSkyDistance(center.separation(tel)))
        return img


__all__ = ["AstrometryOffsets"]
