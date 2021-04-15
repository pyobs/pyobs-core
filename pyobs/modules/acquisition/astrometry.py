import logging
from typing import Union, Tuple
from astropy.wcs import WCS

from pyobs.object import get_object
from pyobs.images.processors.astrometry import Astrometry
from pyobs.images import Image
from pyobs.images.processors.detection import SourceDetection
from .base import BaseAcquisition

log = logging.getLogger(__name__)


class AstrometryAcquisition(BaseAcquisition):
    """Module for acquiring telescope using astrometry."""

    def __init__(self, source_detection: Union[dict, SourceDetection], astrometry: Union[dict, Astrometry],
                 *args, **kwargs):
        """Acquire using astrometry.

        Args:
            source_detection: Source detection class to use.
            astrometry: Astrometry class to use.
        """
        BaseAcquisition.__init__(self, *args, **kwargs)
        self._source_detection = source_detection
        self._astrometry = astrometry

    def _get_target_radec(self, img: Image, ra: float, dec: float) -> Tuple[float, float]:
        """Returns RA/Dec coordinates of pixel that needs to be centered.

        Params:
            img: Image to analyze.
            ra: Requested RA.
            dec: Requested Declination.

        Returns:
            (ra, dec) of pixel that needs to be moved to the centre of the image.

        Raises:
            ValueError: If target coordinates could not be determined.
        """

        # get objects
        source_detection = get_object(self._source_detection, SourceDetection)
        astrometry = get_object(self._astrometry, Astrometry)

        # copy image
        image = img.copy()

        # find stars
        log.info('Searching for stars...')
        source_detection(image)
        if len(image.catalog) == 0:
            raise ValueError('Could not find any stars in image.')
        log.info('Found %d stars.' % len(image.catalog))

        # do astrometry
        log.info('Calculating astrometric solution...')
        astrometry(image)
        if image.header['WCSERR'] == 1:
            raise ValueError('Could not find astrometric solution.')

        # get WCS on new image return x/y coordinates of requested RA/Dec
        wcs = WCS(image.header)
        return wcs.all_world2pix(ra, dec, 0)


__all__ = ['AstrometryAcquisition']
