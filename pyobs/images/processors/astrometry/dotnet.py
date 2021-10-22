import logging
from typing import Any

import requests
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u

from pyobs.images import Image
from .astrometry import Astrometry


log = logging.getLogger(__name__)


class AstrometryDotNet(Astrometry):
    """Perform astrometry using astrometry.net"""
    __module__ = 'pyobs.images.processors.astrometry'

    def __init__(self, url: str, source_count: int = 50, radius: float = 3., **kwargs: Any):
        """Init new astronomy.net processor.

        Args:
            url: URL to service.
            source_count: Number of sources to send.
            radius: Radius to search in.
        """
        Astrometry.__init__(self, **kwargs)

        # URL to web-service
        self.url = url
        self.source_count = source_count
        self.radius = radius

    def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.

        Writes WCSERR=1 into FITS header on failure.

        Args:
            image: Image to analyse.
        """

        # copy image
        img = image.copy()

        # get catalog
        if img.catalog is None:
            log.warning('No catalog found in image.')
            return image
        cat = img.catalog[['x', 'y', 'flux']].to_pandas().dropna()

        # nothing?
        if cat is None or len(cat) < 3:
            log.warning('Not enough sources for astrometry.')
            img.header['WCSERR'] = 1
            return img

        # sort it and take N brightest sources
        cat = cat.sort_values('flux', ascending=False)
        cat = cat[:self.source_count]

        # no CDELT1?
        if 'CDELT1' not in img.header:
            log.warning('No CDELT1 found in header.')
            img.header['WCSERR'] = 1
            return img

        # build request data
        scale = abs(img.header['CDELT1']) * 3600
        data = {
            'ra': img.header['TEL-RA'],
            'dec': img.header['TEL-DEC'],
            'scale_low': scale * 0.9,
            'scale_high': scale * 1.1,
            'radius': self.radius,
            'nx': img.header['NAXIS1'],
            'ny': img.header['NAXIS2'],
            'x': cat['x'].tolist(),
            'y': cat['y'].tolist(),
            'flux': cat['flux'].tolist()
        }

        # log it
        ra_dec = SkyCoord(ra=data['ra'] * u.deg, dec=data['dec'] * u.deg, frame='icrs')
        cx, cy = img.header['CRPIX1'], img.header['CRPIX2']
        log.info('Found original RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.',
                 ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True), data['ra'],
                 ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True), data['dec'],
                 cx, cy)

        # send it
        r = requests.post(self.url, json=data)

        # success?
        if r.status_code != 200 or 'error' in r.json():
            # set error
            img.header['WCSERR'] = 1
            if 'error' in r.json():
                # "Could not find WCS file." is just an info, which means that WCS was not successful
                if r.json()['error'] == 'Could not find WCS file.':
                    log.info('Could not determine WCS.')
                else:
                    log.warning('Received error from astrometry service: %s', r.json()['error'])
            else:
                log.error('Could not connect to astrometry service.')
            return img

        else:
            # copy keywords
            hdr = r.json()
            header_keywords_to_update = ['CTYPE1', 'CTYPE2', 'CRPIX1', 'CRPIX2', 'CRVAL1',
                                         'CRVAL2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2']
            for keyword in header_keywords_to_update:
                img.header[keyword] = hdr[keyword]

            # astrometry.net gives a CD matrix, so we have to delete the PC matrix and the CDELT* parameters
            for keyword in ['PC1_1', 'PC1_2', 'PC2_1', 'PC2_2', 'CDELT1', 'CDELT2']:
                del img.header[keyword]

            # calculate world coordinates for all sources in catalog
            image_wcs = WCS(img.header)
            ras, decs = image_wcs.all_pix2world(img.catalog['x'], img.catalog['y'], 1)

            # set them
            img.catalog['ra'] = ras
            img.catalog['dec'] = decs

            # RA/Dec at center pos
            final_ra, final_dec = image_wcs.all_pix2world(cx, cy, 0)
            ra_dec = SkyCoord(ra=final_ra * u.deg, dec=final_dec * u.deg, frame='icrs')

            # log it
            log.info('Found final RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.',
                     ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True), data['ra'],
                     ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True), data['dec'],
                     cx, cy)

            # success
            img.header['WCSERR'] = 0

        # finished
        return img


__all__ = ['AstrometryDotNet']
