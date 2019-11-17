import logging
import requests
from astropy.wcs import WCS

from pyobs.utils.images import Image
from .astrometry import Astrometry


log = logging.getLogger(__name__)


class AstrometryDotNet(Astrometry):
    def __init__(self, url: str, source_count: int = 50, *args, **kwargs):
        Astrometry.__init__(self, *args, **kwargs)

        # URL to web-service
        self.url = url
        self.source_count = source_count

    def __call__(self, image: Image):
        # get catalog
        cat = image.catalog

        # sort it and take N brightest sources
        cat.sort(['flux'], reverse=True)
        cat = cat[:self.source_count]

        # build request data
        scale = abs(image.header['CDELT1']) * 3600
        data = {
            'ra': image.header['TEL-RA'],
            'dec': image.header['TEL-DEC'],
            'scale_low': scale * 0.9,
            'scale_high': scale * 1.1,
            'nx': image.header['NAXIS1'],
            'ny': image.header['NAXIS2'],
            'x': cat['x'].tolist(),
            'y': cat['y'].tolist(),
            'flux': cat['flux'].tolist()
        }

        # send it
        r = requests.post('https://astrometry.monet.uni-goettingen.de/', json=data)

        # success?
        if r.status_code != 200 or 'error' in r.json():
            # set error
            image.header['WCSERR'] = 1

        else:
            # copy keywords
            hdr = r.json()
            header_keywords_to_update = ['CTYPE1', 'CTYPE2', 'CRPIX1', 'CRPIX2', 'CRVAL1',
                                         'CRVAL2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2']
            for keyword in header_keywords_to_update:
                image.header[keyword] = hdr[keyword]

            # astrometry.net gives a CD matrix, so we have to delete the PC matrix and the CDELT* parameters
            for keyword in ['PC1_1', 'PC1_2', 'PC2_1', 'PC2_2', 'CDELT1', 'CDELT2']:
                del image.header[keyword]

            # calculate world coordinates for all sources in catalog
            image_wcs = WCS(image.header)
            ras, decs = image_wcs.all_pix2world(image.catalog['x'], image.catalog['y'], 1)

            # set them
            image.catalog['ra'] = ras
            image.catalog['dec'] = decs

            # success
            image.header['WCSERR'] = 0


__all__ = ['AstrometryDotNet']
