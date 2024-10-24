import logging
from typing import Any
import numpy as np
from astropy.coordinates import EarthLocation, AltAz, Angle
import astropy.units as u

from pyobs.images import Image
from .applyoffsets import ApplyOffsets
from ..time import Time
from ...images.meta import AltAzOffsets, RaDecOffsets, PixelOffsets
from ...interfaces import ITelescope, IOffsetsAltAz

log = logging.getLogger(__name__)


class ApplyAltAzOffsets(ApplyOffsets):
    """Apply offsets from a given image to a given telescope."""

    __module__ = "pyobs.utils.offsets"

    def __init__(self, min_offset: float = 0.5, max_offset: float = 30, **kwargs: Any):
        """Initializes a new ApplyAltAzOffsets.

        Args:
            min_offset: Min offset in arcsec to move.
            max_offset: Max offset in arcsec to move.
        """
        ApplyOffsets.__init__(self, **kwargs)

        # store
        self._min_offset = min_offset
        self._max_offset = max_offset

    async def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation) -> bool:
        """Take the pixel offsets stored in the meta data of the image and apply them to the given telescope.

        Args:
            image: Image to take offsets and WCS from.
            telescope: Telescope to apply offsets to.
            location: Observer location on Earth.

        Returns:
            Whether offsets have been applied successfully.
        """

        # telescope must be of type IAltAzOffsets
        tel = telescope
        if not isinstance(telescope, IOffsetsAltAz):
            log.error("Given telescope cannot handle Alt/Az offsets.")
            return False

        # what kind of offsets to we have?
        if image.has_meta(AltAzOffsets):
            # offsets are Alt/Az, so get them directly
            offsets = image.get_meta(AltAzOffsets)
            log.info("Found Alt/Az shift of dalt=%.2f, daz=%.2f.", offsets.dalt, offsets.daz)
            dalt, daz = Angle(offsets.dalt * u.arcsec), Angle(offsets.daz * u.arcsec)

        elif image.has_meta(RaDecOffsets):
            raise NotImplementedError()

        elif image.has_meta(PixelOffsets):
            # get RA/Dec coordinates of center and center+offsets
            try:
                radec_center, radec_target = self._get_radec_center_target(image, location)
            except ValueError:
                log.warning("Could not get offsets from image meta.")
                return False

            # convert to Alt/Az
            frame = AltAz(obstime=Time(image.header["DATE-OBS"]), location=location)
            altaz_center = radec_center.transform_to(frame)
            altaz_target = radec_target.transform_to(frame)

            # get offset
            daz, dalt = altaz_center.spherical_offsets_to(altaz_target)
            log.info('Transformed to Alt/Az shift of dAlt=%.2f", dAz=%.2f".', dalt.arcsec, daz.arcsec)

        else:
            raise ValueError("No offsets found.")

        # get current offset
        cur_dalt, cur_daz = await telescope.get_offsets_altaz()

        # log it
        await self._log_offset(tel, "dalt", cur_dalt, dalt.degree, "daz", cur_daz, daz.degree)

        # too large or too small?
        diff = np.sqrt(dalt.arcsec**2.0 + daz.arcsec**2)
        if diff < self._min_offset:
            log.warning("Shift too small, skipping auto-guiding for now...")
            return False
        if diff > self._max_offset:
            log.warning("Shift too large, skipping auto-guiding for now...")
            return False

        # move offset
        log.info("Offsetting telescope...")
        await telescope.set_offsets_altaz(float(cur_dalt + dalt.degree), float(cur_daz + daz.degree))
        return True


__all__ = ["ApplyAltAzOffsets"]
