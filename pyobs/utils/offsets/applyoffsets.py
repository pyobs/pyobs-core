from typing import Tuple
import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.wcs import WCS
import logging

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from pyobs.interfaces import ITelescope, IPointingRaDec, IPointingAltAz
from pyobs.object import Object
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class ApplyOffsets(Object):
    """Apply offsets from a given image to a given telescope."""
    __module__ = 'pyobs.utils.offsets'

    def __init__(self, log_file: str = None, log_absolute: bool = False, *args, **kwargs):
        Object.__init__(self, *args, **kwargs)

        # init log file
        self._publisher = None if log_file is None else CsvPublisher(log_file)
        self._log_absolute = log_absolute

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
        offsets = image.get_meta(PixelOffsets)
        log.info('Found pixel shift of dx=%.2f, dy=%.2f.', offsets.dx, offsets.dy)

        # get reference pixel and date obs
        cx, cy = image.header['DET-CPX1'], image.header['DET-CPX2']

        # get WCS and RA/DEC for pixel and pixel + dx/dy
        w = WCS(image.header)
        center = w.pixel_to_world(cx, cy)
        target = w.pixel_to_world(cx + offsets.dx, cy + offsets.dy)
        return center, target

    def _log_offset(self, telescope: ITelescope, x_header: str, x_cur: float, x_delta: float,
                    y_header: str, y_cur: float, y_delta: float):
        """Logs offset.

        Args:
            entry: Entry to log.
        """

        # nothing?
        if self._publisher is None:
            return

        # init
        log_entry = {'datetime': Time.now().isot}

        # RA/Dec?
        if isinstance(telescope, IPointingRaDec):
            log_entry['ra'], log_entry['dec'] = telescope.get_radec().wait()

        # Alt/Az?
        if isinstance(telescope, IPointingAltAz):
            log_entry['alt'], log_entry['az'] = telescope.get_altaz().wait()

        # add entry
        log_entry[x_header] = x_delta + (x_cur if self._log_absolute else 0.)
        log_entry[y_header] = y_delta + (y_cur if self._log_absolute else 0.)

        # add separation (assume Euclidian space)
        log_entry['separation'] = np.sqrt(log_entry[x_header]**2 + log_entry[y_header]**2)

        # log it
        self._publisher(**log_entry)


__all__ = ['ApplyOffsets']
