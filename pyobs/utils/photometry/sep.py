from astropy.table import Table
import logging
import numpy as np

from .photometry import Photometry
from pyobs.utils.images import Image

log = logging.getLogger(__name__)


class SepPhotometry(Photometry):
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
            *args:
            **kwargs:
        """

        Photometry.__init__(self, *args, **kwargs)

        # test imports
        import sep

        # store
        self.threshold = threshold
        self.minarea = minarea
        self.deblend_nthresh = deblend_nthresh
        self.deblend_cont = deblend_cont
        self.clean = clean
        self.clean_param = clean_param

    def find_stars(self, image: Image) -> Table:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Full table with results.
        """
        import sep

        # get data and make it continuous
        data = image.data.copy()

        # estimate background, probably we need to byte swap, and subtract it
        try:
            bkg = sep.Background(data)
        except ValueError as e:
            data = data.byteswap(True).newbyteorder()
            bkg = sep.Background(data)
        bkg.subfrom(data)

        # mask?
        mask = image.mask.data if image.mask is not None else None

        # extract sources
        try:
            sources = sep.extract(data, self.threshold, err=bkg.globalrms, minarea=self.minarea,
                                  deblend_nthresh=self.deblend_nthresh, deblend_cont=self.deblend_cont,
                                  clean=self.clean, clean_param=self.clean_param, mask=mask)
        except:
            log.exception('An error has occured.')
            return Table()

        # convert to astropy table
        sources = Table(sources)

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]

        # Calculate the ellipticity
        sources['ellipticity'] = 1.0 - (sources['b'] / sources['a'])

        # get gain
        gain = image.header['DET-GAIN'] if 'DET-GAIN' in image.header else None

        # Kron radius
        kronrad, krflag = sep.kron_radius(data, sources['x'], sources['y'], sources['a'], sources['b'],
                                          sources['theta'], 6.0)
        sources['flag'] |= krflag
        sources['kronrad'] = kronrad

        # equivalent of FLUX_AUTO
        flux, fluxerr, flag = sep.sum_ellipse(data, sources['x'], sources['y'], sources['a'], sources['b'],
                                              sources['theta'], 2.5 * kronrad, subpix=1, mask=mask,
                                              err=bkg.rms(), gain=gain)
        sources['flag'] |= flag
        sources['flux'] = flux
        sources['fluxerr'] = fluxerr

        # equivalent to FLUX_RADIUS
        sources['radius'], _ = sep.flux_radius(data, sources['x'], sources['y'], 6. * sources['a'], 0.5,
                                               normflux=sources['flux'], subpix=5)

        # radii at 0.25, 0.5, and 0.75 flux
        flux_radii, flag = sep.flux_radius(data, sources['x'], sources['y'], 6.0 * sources['a'], [0.25, 0.5, 0.75],
                                           normflux=sources['flux'], subpix=5)
        sources['flag'] |= flag
        sources['fluxrad25'] = flux_radii[:, 0]
        sources['fluxrad50'] = flux_radii[:, 1]
        sources['fluxrad75'] = flux_radii[:, 2]

        # xwin/ywin
        sig = 2. / 2.35 * sources['fluxrad50']
        xwin, ywin, flag = sep.winpos(data, sources['x'], sources['y'], sig)
        sources['flag'] |= flag
        sources['xwin'] = xwin
        sources['ywin'] = ywin

        # perform aperture photometry for diameters of 1" to 4"
        for diameter in [1, 2, 3, 4]:
            flux, fluxerr, flag = sep.sum_circle(data, sources['x'], sources['y'],
                                                 diameter / 2. / image.pixel_scale,
                                                 mask=mask, err=bkg.rms(), gain=gain)
            sources['fluxaper{0}'.format(diameter)] = flux
            sources['fluxerr{0}'.format(diameter)] = fluxerr
            sources['flag'] |= flag

        # match fits conventions
        sources['x'] += 1.0
        sources['y'] += 1.0
        sources['xpeak'] += 1
        sources['ypeak'] += 1
        sources['xwin'] += 1.0
        sources['ywin'] += 1.0
        sources['theta'] = np.degrees(sources['theta'])

        # pick columns for catalog
        cat = sources['x', 'y', 'xwin', 'ywin', 'xpeak', 'ypeak',
                      'flux', 'fluxerr', 'peak', 'fluxaper1', 'fluxerr1',
                      'fluxaper2', 'fluxerr2', 'fluxaper3', 'fluxerr3',
                      'fluxaper4', 'fluxerr4', 'fwhm',
                      'a', 'b', 'theta', 'kronrad', 'ellipticity',
                      'fluxrad25', 'fluxrad50', 'fluxrad75',
                      'x2', 'y2', 'xy', 'flag']

        # set it
        image.catalog = cat

        # return full catalog
        return sources


__all__ = ['SepPhotometry']
