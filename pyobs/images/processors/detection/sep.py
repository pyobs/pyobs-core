from __future__ import annotations
from typing import Tuple
from astropy.table import Table
import logging
import numpy as np

from .sourcedetection import SourceDetection
from pyobs.images import Image

log = logging.getLogger(__name__)


class SepSourceDetection(SourceDetection):
    """Detect sources using SEP."""
    __module__ = 'pyobs.images.processors.detection'

    def __init__(self, threshold: float = 1.5, minarea: int = 5, deblend_nthresh: int = 32,
                 deblend_cont: float = 0.005, clean: bool = True, clean_param: float = 1.0, *args, **kwargs):
        """Initializes a wrapper for SEP. See its documentation for details.

        Highly inspired by LCO's wrapper for SEP, see:
        https://github.com/LCOGT/banzai/blob/master/banzai/photometry.py

        Args:
            threshold: Threshold pixel value for detection.
            minarea: Minimum number of pixels required for detection.
            deblend_nthresh: Number of thresholds used for object deblending.
            deblend_cont: Minimum contrast ratio used for object deblending.
            clean: Perform cleaning?
            clean_param: Cleaning parameter (see SExtractor manual).
        """

        # store
        self.threshold = threshold
        self.minarea = minarea
        self.deblend_nthresh = deblend_nthresh
        self.deblend_cont = deblend_cont
        self.clean = clean
        self.clean_param = clean_param

    def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """
        import sep

        # remove background
        data, bkg = SepSourceDetection.remove_background(image.data, image.mask)

        # extract sources
        sources = sep.extract(data, self.threshold, err=bkg.globalrms, minarea=self.minarea,
                              deblend_nthresh=self.deblend_nthresh, deblend_cont=self.deblend_cont,
                              clean=self.clean, clean_param=self.clean_param, mask=image.mask)

        # convert to astropy table
        sources = Table(sources)

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]
        x, y = sources['x'], sources['y']

        # Calculate the ellipticity
        sources['ellipticity'] = 1.0 - (sources['b'] / sources['a'])

        # calculate the FWHMs of the stars
        fwhm = 2.0 * (np.log(2) * (sources['a'] ** 2.0 + sources['b'] ** 2.0)) ** 0.5
        sources['fwhm'] = fwhm

        # theta in degrees
        sources['theta'] = np.degrees(sources['theta'])

        # Kron radius
        kronrad, krflag = sep.kron_radius(data, x, y, sources['a'], sources['b'], sources['theta'], 6.0)
        sources['flag'] |= krflag
        sources['kronrad'] = kronrad

        # equivalent of FLUX_AUTO
        gain = image.header['DET-GAIN'] if 'DET-GAIN' in image.header else None
        flux, fluxerr, flag = sep.sum_ellipse(data, x, y, sources['a'], sources['b'],
                                              np.radians(sources['theta']), 2.5 * kronrad,
                                              subpix=1, mask=image.mask, gain=gain)
        sources['flag'] |= flag
        sources['flux'] = flux

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]

        # match fits conventions
        sources['x'] += 1
        sources['y'] += 1

        # pick columns for catalog
        cat = sources['x', 'y', 'peak', 'flux', 'fwhm', 'a', 'b', 'theta', 'ellipticity', 'npix', 'kronrad']

        # copy image, set catalog and return it
        img = image.copy()
        img.catalog = cat
        return img

    @staticmethod
    def remove_background(data: np.ndarray, mask: np.ndarray = None) -> Tuple[np.ndarray, 'sep.Background']:
        """Remove background from image in data.

        Args:
            data: Data to remove background from.
            mask: Mask to use for estimating background.

        Returns:
            Image without background.
        """
        import sep

        # get data and make it continuous
        d = data.astype(np.float)

        # estimate background, probably we need to byte swap
        try:
            bkg = sep.Background(d, mask=mask, bw=32, bh=32, fw=3, fh=3)
        except ValueError as e:
            d = d.byteswap(True).newbyteorder()
            bkg = sep.Background(d, mask=mask, bw=32, bh=32, fw=3, fh=3)

        # subtract it
        bkg.subfrom(d)

        # return data without background and background
        return d, bkg


__all__ = ['SepSourceDetection']
