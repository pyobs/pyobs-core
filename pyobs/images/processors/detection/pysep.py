from __future__ import annotations
from typing import Tuple, TYPE_CHECKING, Any, Optional
from astropy.table import Table
import logging
import numpy as np
import pandas as pd

from .sourcedetection import SourceDetection
from pyobs.images import Image
if TYPE_CHECKING:
    from sep import Background

log = logging.getLogger(__name__)


class SepSourceDetection(SourceDetection):
    """Detect sources using SEP."""
    __module__ = 'pyobs.images.processors.detection'

    def __init__(self, threshold: float = 1.5, minarea: int = 5, deblend_nthresh: int = 32,
                 deblend_cont: float = 0.005, clean: bool = True, clean_param: float = 1.0, **kwargs: Any):
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
        SourceDetection.__init__(self, **kwargs)

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

        # got data?
        if image.data is None:
            log.warning('No data found in image.')
            return image

        # no mask?
        mask = image.mask if image.mask is not None else np.ones(image.data.shape, dtype=bool)

        # remove background
        data, bkg = SepSourceDetection.remove_background(image.data, mask)

        # extract sources
        sources = sep.extract(data, self.threshold, err=bkg.globalrms, minarea=self.minarea,
                              deblend_nthresh=self.deblend_nthresh, deblend_cont=self.deblend_cont,
                              clean=self.clean, clean_param=self.clean_param, mask=image.mask)

        # convert to astropy table
        sources = pd.DataFrame(sources)

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]
        x, y = sources['x'], sources['y']

        # Calculate the ellipticity
        sources['ellipticity'] = 1.0 - (sources['b'] / sources['a'])

        # calculate the FWHMs of the stars
        fwhm = 2.0 * (np.log(2) * (sources['a'] ** 2.0 + sources['b'] ** 2.0)) ** 0.5
        sources['fwhm'] = fwhm

        # clip theta to [-pi/2,pi/2]
        sources['theta'] = sources['theta'].clip(lower=np.pi/2, upper=np.pi/2)

        # Kron radius
        kronrad, krflag = sep.kron_radius(data, x, y, sources['a'], sources['b'], sources['theta'], 6.0)
        sources['flag'] |= krflag
        sources['kronrad'] = kronrad

        # equivalent of FLUX_AUTO
        gain = image.header['DET-GAIN'] if 'DET-GAIN' in image.header else None
        flux, fluxerr, flag = sep.sum_ellipse(data, x, y, sources['a'], sources['b'],
                                              sources['theta'], 2.5 * kronrad,
                                              subpix=1, mask=image.mask, gain=gain)
        sources['flag'] |= flag
        sources['flux'] = flux

        # radii at 0.25, 0.5, and 0.75 flux
        flux_radii, flag = sep.flux_radius(data, x, y, 6.0 * sources['a'],
                                           [0.25, 0.5, 0.75], normflux=sources['flux'], subpix=5)
        sources['flag'] |= flag
        sources['fluxrad25'] = flux_radii[:, 0]
        sources['fluxrad50'] = flux_radii[:, 1]
        sources['fluxrad75'] = flux_radii[:, 2]

        # xwin/ywin
        sig = 2. / 2.35 * sources['fluxrad50']
        xwin, ywin, flag = sep.winpos(data, x, y, sig)
        sources['flag'] |= flag
        sources['xwin'] = xwin
        sources['ywin'] = ywin

        # theta in degrees
        sources['theta'] = np.degrees(sources['theta'])

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]

        # match fits conventions
        sources['x'] += 1
        sources['y'] += 1

        # pick columns for catalog
        cat = sources[['x', 'y', 'peak', 'flux', 'fwhm', 'a', 'b', 'theta', 'ellipticity', 'tnpix', 'kronrad',
                      'fluxrad25', 'fluxrad50', 'fluxrad75', 'xwin', 'ywin']]

        # copy image, set catalog and return it
        img = image.copy()
        img.catalog = Table.from_pandas(cat)
        return img

    @staticmethod
    def remove_background(data: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, 'Background']:
        """Remove background from image in data.

        Args:
            data: Data to remove background from.
            mask: Mask to use for estimating background.

        Returns:
            Image without background.
        """
        import sep

        # get data and make it continuous
        d = data.astype(float)

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
