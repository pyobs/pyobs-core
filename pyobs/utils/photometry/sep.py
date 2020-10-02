from astropy.table import Table
import logging

from .photometry import Photometry
from pyobs.utils.images import Image


log = logging.getLogger(__name__)


class SepPhotometry(Photometry):
    def __init__(self, threshold: float = 1.5, minarea: int = 5, deblend_nthresh: int = 32,
                 deblend_cont: float = 0.005, clean: bool = True, clean_param: float = 1.0, *args, **kwargs):
        """Initializes a wrapper for SEP. See its documentation for details.

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

        # equivalent of FLUX_AUTO
        kronrad, krflag = sep.kron_radius(data, sources['x'], sources['y'], sources['a'], sources['b'],
                                          sources['theta'], 6.0)
        flux, fluxerr, flag = sep.sum_ellipse(data, sources['x'], sources['y'], sources['a'], sources['b'],
                                          sources['theta'], 2.5 * kronrad, subpix=1)
        sources['flux_auto'] = flux
        sources['flux_auto_err'] = fluxerr

        # equivalent to FLUX_RADIUS
        sources['radius'], _ = sep.flux_radius(data, sources['x'], sources['y'], 6. * sources['a'], 0.5,
                                               normflux=sources['flux_auto'], subpix=5)

        # pick columns for catalog
        cat = sources['x', 'y', 'ellipticity', 'flux', 'flux_auto', 'flux_auto_err', 'radius']

        # set it
        image.catalog = cat

        # return full catalog
        return sources


__all__ = ['SepPhotometry']
