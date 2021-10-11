from typing import Tuple

from astropy.table import Table
import logging
import numpy as np

from .sourcedetection import SourceDetection
from pyobs.images import Image

log = logging.getLogger(__name__)


class DaophotSourceDetection(SourceDetection):
    """Detect source using Daophot."""
    __module__ = 'pyobs.images.processors.detection'

    def __init__(self, fwhm: float = 3., threshold: float = 4., bkg_sigma: float = 3.,
                 bkg_box_size: Tuple[int, int] = (50, 50), bkg_filter_size: Tuple[int, int] = (3, 3),
                 *args, **kwargs):
        """Initializes a wrapper for photutils. See its documentation for details.

        Args:
            fwhm: Full-width at half maximum for Gaussian kernel.
            threshold: Threshold pixel value for detection.
            bkg_sigma: Sigma for background kappa-sigma clipping.
            bkg_box_size: Box size for background estimation.
            bkg_filter_size: Filter size for background estimation.
        """
        SourceDetection.__init__(self, *args, **kwargs)

        # store
        self.fwhm = fwhm
        self.threshold = threshold
        self.bkg_sigma = bkg_sigma
        self.bkg_box_size = bkg_box_size
        self.bkg_filter_size = bkg_filter_size

    def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """
        from astropy.stats import SigmaClip, sigma_clipped_stats
        from photutils import Background2D, MedianBackground, DAOStarFinder

        # get data
        data = image.data.astype(np.float).copy()

        # estimate background
        sigma_clip = SigmaClip(sigma=self.bkg_sigma)
        bkg_estimator = MedianBackground()
        bkg = Background2D(data, self.bkg_box_size, filter_size=self.bkg_filter_size,
                           sigma_clip=sigma_clip, bkg_estimator=bkg_estimator, mask=image.mask)
        data -= bkg.background

        # do statistics
        mean, median, std = sigma_clipped_stats(data, sigma=3.0)

        # find stars
        daofind = DAOStarFinder(fwhm=self.fwhm, threshold=self.threshold * std)
        sources = daofind(data - median)

        # rename columns
        sources.rename_column('xcentroid', 'x')
        sources.rename_column('ycentroid', 'y')

        # match fits conventions
        sources['x'] += 1
        sources['y'] += 1

        # pick columns for catalog
        cat = sources['x', 'y', 'flux', 'peak']

        # copy image, set catalog and return it
        img = image.copy()
        img.catalog = cat
        return img


__all__ = ['DaophotSourceDetection']
