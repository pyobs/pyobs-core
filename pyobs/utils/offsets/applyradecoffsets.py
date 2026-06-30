import logging
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import Angle, EarthLocation

from pyobs.images import Image

from ...images.meta import AltAzOffsets, PixelOffsets, RaDecOffsets
from ...interfaces import IOffsetsRaDec, ITelescope, RaDecOffsetState
from .applyoffsets import ApplyOffsets

log = logging.getLogger(__name__)


class ApplyRaDecOffsets(ApplyOffsets):
    """Apply offsets from a given image to a given telescope."""

    __module__ = "pyobs.utils.offsets"

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

    async def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation | None) -> bool:
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
            log.error("Given telescope cannot handle RA/Dec offsets.")
            return False

        # what kind of offsets to we have?
        if image.has_meta(RaDecOffsets):
            # offsets are RA/Dec, so get them directly
            offsets = image.get_meta(RaDecOffsets)
            log.info("Found RA/Dec shift of dra=%.2f, ddec=%.2f.", offsets.dra, offsets.ddec)
            dra, ddec = Angle(offsets.dra * u.arcsec), Angle(offsets.ddec * u.arcsec)

        elif image.has_meta(AltAzOffsets):
            raise NotImplementedError()

        elif image.has_meta(PixelOffsets):
            # get RA/Dec coordinates of center and center+offsets
            try:
                radec_center, radec_target = self._get_radec_center_target(image, location)
            except ValueError:
                log.warning("Could not get offsets from image meta.")
                return False

            # get offset
            dra, ddec = radec_center.spherical_offsets_to(radec_target)
            log.info('Transformed to RA/Dec shift of dRA=%.2f", dDec=%.2f".', dra.arcsec, ddec.arcsec)

        else:
            raise ValueError("No offsets found.")

        # get current offset
        off_state: RaDecOffsetState | None = telescope.get_state(IOffsetsRaDec)
        cur_dra, cur_ddec = (off_state.ra, off_state.dec) if off_state is not None else (0.0, 0.0)

        # log it
        await self._log_offset(tel, "dra", cur_dra, dra.degree, "ddec", cur_ddec, ddec.degree)

        # too large or too small?
        diff = np.sqrt(dra.arcsec**2.0 + ddec.arcsec**2)
        if diff < self._min_offset:
            log.warning("Shift too small, skipping auto-guiding for now...")
            return False
        if diff > self._max_offset:
            log.warning("Shift too large, skipping auto-guiding for now...")
            return False

        # move offset
        log.info("Offsetting telescope...")
        await telescope.set_offsets_radec(float(cur_dra + dra.degree), float(cur_ddec + ddec.degree))
        return True


__all__ = ["ApplyRaDecOffsets"]
