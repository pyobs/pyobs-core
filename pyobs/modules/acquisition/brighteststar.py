import logging
from astropy.stats import sigma_clipped_stats
from photutils import DAOStarFinder

from .base import BaseAcquisition
from ...utils.images import Image

log = logging.getLogger(__name__)


class BrightestStarAcquisition(BaseAcquisition):
    """Module for acquiring telescope on brightest star in field."""

    def _get_target_pixel(self, img: Image, ra: float, dec: float) -> (float, float):
        """Returns RA/Dec coordinates of pixel that needs to be centered.

        Params:
            img: Image to analyze.
            ra: Requested RA.
            dec: Requested Declination.

        Returns:
            (x, y) of pixel that needs to be moved to the centre of the image.
        """

        # do statistics on image
        mean, median, std = sigma_clipped_stats(img.data, sigma=3.0)

        # find stars
        daofind = DAOStarFinder(fwhm=3.0, threshold=5. * std)
        sources = daofind(img.data - median).to_pandas()

        # sort by flux
        sources.sort_values('flux', ascending=False, inplace=True)

        # target is first one in list
        target = sources.iloc[0]
        log.info('Found brightest star at x=%.2f, y=%.2f.', target['xcentroid'], target['ycentroid'])
        return target['xcentroid'], target['ycentroid']


__all__ = ['BrightestStarAcquisition']
