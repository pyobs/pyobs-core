import logging
from typing import Any

import numpy as np
from astropy.coordinates import EarthLocation

from pyobs.images import Image
from .applyoffsets import ApplyOffsets
from ...interfaces import ITelescope, IOffsetsRaDec

log = logging.getLogger(__name__)


class ApplyRaDecOffsets(ApplyOffsets):
    """Apply offsets from a given image to a given telescope."""
    __module__ = 'pyobs.utils.offsets'

    def __init__(self, min_offset: float = 0.5, max_offset: float = 30, **kwargs: Any):
        """Initializes a new ApplyRaDecOffsets.

        Args:
            min_offset: Min offset in arcsec to move.
            max_offset: Max offset in arcsec to move.
        """
        ApplyOffsets.__init__(self, **kwargs)

        # store
        self._min_offset = min_offset
        self._max_offset = max_offset

    def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation) -> bool:
        """Take the pixel offsets stored in the meta data of the image and apply them to the given telescope.

        Args:
            image: Image to take offsets and WCS from.
            telescope: Telescope to apply offsets to.
            location: Observer location on Earth.

        Returns:
            Whether offsets have been applied successfully.
        """

        # telescope must be of type IRaDecOffsets
        tel = telescope
        if not isinstance(telescope, IOffsetsRaDec):
            log.error('Given telescope cannot handle RA/Dec offsets.')
            return False

        # get RA/Dec coordinates of center and center+offsets
        try:
            radec_center, radec_target = self._get_radec_center_target(image, location)
        except ValueError:
            log.error('Could not get offsets from image meta.')
            return False

        # get offset
        dra, ddec = radec_center.spherical_offsets_to(radec_target)
        log.info('Transformed to RA/Dec shift of dRA=%.2f", dDec=%.2f".', dra.arcsec, ddec.arcsec)

        # get current offset
        cur_dra, cur_ddec = telescope.get_offsets_radec().wait()

        # log it
        self._log_offset(tel, 'dra', cur_dra, dra.degree, 'ddec', cur_ddec, ddec.degree)

        # too large or too small?
        diff = np.sqrt(dra.arcsec**2. + ddec.arcsec**2)
        if diff < self._min_offset:
            log.warning('Shift too small, skipping auto-guiding for now...')
            return False
        if diff > self._max_offset:
            log.warning('Shift too large, skipping auto-guiding for now...')
            return False

        # move offset
        log.info('Offsetting telescope...')
        telescope.set_offsets_radec(float(cur_dra + dra.degree), float(cur_ddec + ddec.degree)).wait()
        return True


__all__ = ['ApplyRaDecOffsets']
