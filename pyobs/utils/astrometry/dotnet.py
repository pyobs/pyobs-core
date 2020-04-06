import logging
import requests
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u

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

        # nothing?
        if cat is None or len(cat) < 3:
            log.error('Not enough sources for astrometry.')
            image.header['WCSERR'] = 1
            return

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

        # log it
        ra_dec = SkyCoord(ra=data['ra'] * u.deg, dec=data['dec'] * u.deg, frame='icrs')
        cx, cy = image.header['CRPIX1'], image.header['CRPIX2']
        log.info('Found original RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.',
                 ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True), data['ra'],
                 ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True), data['dec'],
                 cx, cy)

        # send it
        r = requests.post('https://astrometry.monet.uni-goettingen.de/', json=data)

        # success?
        if r.status_code != 200 or 'error' in r.json():
            # set error
            image.header['WCSERR'] = 1
            if 'error' in r.json():
                log.error('Received error from astrometry service: %s', r.json()['error'])
            else:
                log.error('Could not connect to astrometry service.')

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

            # RA/Dec at center pos
            final_ra, final_dec = image_wcs.all_pix2world(cx, cy, 0)
            ra_dec = SkyCoord(ra=final_ra * u.deg, dec=final_dec * u.deg, frame='icrs')

            # log it
            log.info('Found final RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.',
                     ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True), data['ra'],
                     ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True), data['dec'],
                     cx, cy)

            # success
            image.header['WCSERR'] = 0


__all__ = ['AstrometryDotNet']
