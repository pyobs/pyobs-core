import logging
from typing import Tuple, List
import numpy as np
from astropy.wcs import WCS
from scipy import signal, optimize
from astropy.nddata import NDData
from astropy.table import Table, Column
import photutils

from pyobs.images import Image
from . import Offsets

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class AstrometryOffsets(Offsets):
    """An offset-calculation method based on astrometry. Returns offset to real coordinates."""

    def __init__(self, *args, **kwargs):
        """Initializes new astrometry offsets.

        MUST run after an astrometry processor.
        """
        pass

    def __call__(self, image: Image) -> Image:
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
        x_center, y_center = wcs.all_world2pix(img.header['CRVAL1'], img.header['CRVAL2'], 0)

        # get x/y coordinates from TEL-RA/-DEC, i.e. from where the telescope thought it's pointing
        x_tel, y_tel = wcs.all_world2pix(img.header['TEL-RA'], img.header['TEL-DEC'], 0)

        # calculate offsets as difference between both
        img.meta['offsets'] = x_center - x_tel, y_center - y_tel
        return img


__all__ = ["AstrometryOffsets"]
