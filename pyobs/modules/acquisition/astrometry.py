import logging
from typing import Union
from astropy.io import fits
from astropy.wcs import WCS

from pyobs import get_object
from pyobs.utils.astrometry import Astrometry
from pyobs.utils.images import Image
from pyobs.utils.photometry import Photometry
from .base import BaseAcquisition

log = logging.getLogger(__name__)


class AstrometryAcquisition(BaseAcquisition):
    """Module for acquiring telescope using astrometry."""

    def __init__(self, photometry: Union[dict, Photometry], astrometry: Union[dict, Astrometry], *args, **kwargs):
        """Acquire using astrometry.

        Args:
            photometry: Photometry class to use.
            astrometry: Astrometry class to use.
        """
        BaseAcquisition.__init__(self, *args, **kwargs)
        self._photometry = photometry
        self._astrometry = astrometry

    def _get_target_radec(self, img: Image, ra: float, dec: float) -> (float, float):
        """Returns RA/Dec coordinates of pixel that needs to be centered.

        Params:
            img: Image to analyze.
            ra: Requested RA.
            dec: Requested Declination.

        Returns:
            (ra, dec) of pixel that needs to be moved to the centre of the image.
        """

        # get objects
        photometry = get_object(self._photometry, Photometry)
        astrometry = get_object(self._astrometry, Astrometry)

        # copy image
        image = fits.PrimaryHDU(data=img.data, header=img.header)

        # do photometry and astrometry
        log.info('Searching for stars')
        photometry(image)
        astrometry(image)

        # get WCS on new image return x/y coordinates of requested RA/Dec
        wcs = WCS(image.header)
        return wcs.all_world2pix(ra, dec, 0)


__all__ = ['AstrometryAcquisition']
