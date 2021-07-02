import logging

import numpy as np
from astropy.coordinates import EarthLocation, AltAz

from pyobs.images import Image
from pyobs.interfaces import ITelescope, IAltAzOffsets
from .applyoffsets import ApplyOffsets


log = logging.getLogger(__name__)


class ApplyAltAzOffsets(ApplyOffsets):
    """Apply offsets from a given image to a given telescope."""
    __module__ = 'pyobs.utils.offsets'

    def __init__(self, min_offset: float = 0.5, max_offset: float = 30, *args, **kwargs):
        """Initializes a new ApplyAltAzOffsets.

        Args:
            min_offset: Min offset in arcsec to move.
            max_offset: Max offset in arcsec to move.
        """

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

        # telescope must be of type IAltAzOffsets
        if not isinstance(telescope, IAltAzOffsets):
            log.error('Given telescope cannot handle Alt/Az offsets.')
            return False

        # check offsets in meta
        if 'offsets' not in image.meta:
            log.warning('No offsets found in image meta information.')
            return False

        # get RA/Dec coordinates of center and center+offsets and convert to Alt/Az
        radec_center, radec_target = self._get_radec_center_target(image, location)
        altaz_center = radec_center.transform_to(AltAz)
        altaz_target = radec_target.transform_to(AltAz)

        # get offset
        dalt, daz = altaz_center.spherical_offsets_to(altaz_target)
        log.info('Transformed to Alt/Az shift of dAlt=%.2f", dAz=%.2f".', dalt.arcsec, daz.arcsec)

        # too large or too small?
        diff = np.sqrt(dalt.arcsec**2. + daz.arcsec**2)
        if diff < self._min_offset:
            log.warning('Shift too small, skipping auto-guiding for now...')
            return False
        if diff > self._max_offset:
            log.warning('Shift too large, skipping auto-guiding for now...')
            return False

        # get current offset
        cur_dalt, cur_daz = telescope.get_altaz_offsets().wait()

        # move offset
        log.info('Offsetting telescope...')
        telescope.set_altaz_offsets(float(cur_dalt + dalt.degree), float(cur_daz + daz.degree)).wait()
        return True


__all__ = ['ApplyAltAzOffsets']
