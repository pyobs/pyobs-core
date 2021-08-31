from typing import Tuple
from astropy.coordinates import EarthLocation, SkyCoord
import astropy.units as u
from astropy.wcs import WCS
import logging

from pyobs.images import Image
from pyobs.interfaces import ITelescope
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class ApplyOffsets:
    """Apply offsets from a given image to a given telescope."""
    __module__ = 'pyobs.utils.offsets'

    def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation) -> bool:
        """Take the pixel offsets stored in the meta data of the image and apply them to the given telescope.

        Args:
            image: Image to take offsets and WCS from.
            telescope: Telescope to apply offsets to.
            location: Observer location on Earth.

        Returns:
            Whether offsets have been applied successfully.
        """
        return False

    def _get_radec_center_target(self, image: Image, location: EarthLocation) -> Tuple[SkyCoord, SkyCoord]:
        """Return RA/Dec of central pixel and of central pixel plus offsets.

        Args:
            image: Image to take header and offsets from.
            location: Observer location.

        Returns:
            Tuple of RA/Dec coordinates of center and of centre+offsets.
        """

        # get offsets
        dx, dy = image.meta['offsets']
        if dx is None or dy is None:
            log.info('Either x or y offset (or both) is zero. Not applying them.')
        log.info('Found pixel shift of dx=%.2f, dy=%.2f.', dx, dy)

        # get reference pixel and date obs
        cx, cy = image.header['CRPIX1'], image.header['CRPIX1']
        date_obs = Time(image.header['DATE-OBS'])

        # get WCS and RA/DEC for pixel and pixel + dx/dy
        w = WCS(image.header)
        lon, lat = w.all_pix2world(cx, cy, 0)
        center = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=date_obs, location=location)
        lon, lat = w.all_pix2world(cx + dx, cy + dy, 0)
        target = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=date_obs, location=location)
        return center, target


__all__ = ['ApplyOffsets']
