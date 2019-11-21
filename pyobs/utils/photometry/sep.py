import sep
from astropy.table import Table

from .photometry import Photometry
from pyobs.utils.images import Image


class SepPhotometry(Photometry):
    def __init__(self, threshold=1.5, *args, **kwargs):
        Photometry.__init__(self, *args, **kwargs)
        self.threshold = threshold

    def __call__(self, image: Image) -> Table:
        # get data and make it continuous
        data = image.data.copy()

        # estimate background, probably we need to byte swap, and subtract it
        try:
            bkg = sep.Background(data)
        except ValueError:
            data = data.byteswap(True).newbyteorder()
            bkg = sep.Background(data)
        bkg.subfrom(data)

        # extract sources
        sources = sep.extract(data, self.threshold, err=bkg.globalrms)

        # convert to astropy table
        sources = Table(sources)

        # only keep sources with detection flag < 8
        sources = sources[sources['flag'] < 8]

        # Calculate the ellipticity
        sources['ellipticity'] = 1.0 - (sources['b'] / sources['a'])

        # pick columns for catalog
        cat = sources['x', 'y', 'ellipticity', 'flux']

        # set it
        image.catalog = cat

        # return full catalog
        return sources


__all__ = ['SepPhotometry']
