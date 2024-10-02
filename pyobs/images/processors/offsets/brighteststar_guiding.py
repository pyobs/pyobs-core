import logging
from typing import Tuple, Any, Optional

from astropy.coordinates import Angle, AltAz, EarthLocation
from astropy.table import Table, Row
from astropy.wcs import WCS
from pandas._typing import npt
from pyobs.utils.time import Time
import astropy.units as u

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance, AltAzOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestStarGuiding(Offsets):
    """Calculates offsets from the center of the image to the brightest star."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, center_header_cards: Tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        self._center_header_cards = center_header_cards
        self._ref_image: Optional[Tuple[npt.NDArray[float], npt.NDArray[float]]] = None
        self._ref_pos: Optional[Tuple[float, float]] = None

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        catalog = image.safe_catalog
        if catalog is None or len(catalog) < 1:
            log.warning("No catalog found in image.")
            return image

        if not self._reference_initialized():
            log.info("Initialising auto-guiding with new image...")
            self._ref_image = image
            self._ref_pos = self._get_brightest_star_position(catalog)
            return image

        star_pos = self._get_brightest_star_position(catalog)

        offset = (star_pos[0] - self._ref_pos[0], star_pos[1] - self._ref_pos[1])
        image.set_meta(PixelOffsets(*offset))
        log.info("Found pixel offset of dx=%.2f, dy=%.2f", offset[0], offset[1])

        altaz_offset = self._calc_altaz_offset(image, star_pos)
        image.set_meta(AltAzOffsets(*altaz_offset))
        return image

    def _reference_initialized(self):
        return self._ref_image is not None

    @staticmethod
    def _get_brightest_star_position(catalog: Table) -> Tuple[float, float]:
        brightest_star: Row = max(catalog, key=lambda row: row["flux"])
        log.info("Found brightest star at x=%.2f, y=%.2f", brightest_star["x"], brightest_star["y"])
        return brightest_star["x"], brightest_star["y"]

    def _calc_altaz_offset(self, image: Image, star_pos: Tuple[float, float]):
        radec_ref, radec_target = self._get_radec_ref_target(image, star_pos)
        hdr = image.header
        location = EarthLocation(lat=hdr["LATITUDE"] * u.deg, lon=hdr["LONGITUD"] * u.deg, height=hdr["HEIGHT"] * u.m)
        frame = AltAz(obstime=Time(image.header["DATE-OBS"]), location=location)
        altaz_ref = radec_ref.transform_to(frame)
        altaz_target = radec_target.transform_to(frame)

        # get offset
        daz, dalt = altaz_ref.spherical_offsets_to(altaz_target)

        return dalt.arcsec, daz.arcsec

    def _get_radec_ref_target(self, image: Image, star_pos):
        wcs = WCS(image.header)
        ref = wcs.pixel_to_world(*self._ref_pos)
        target = wcs.pixel_to_world(*star_pos)
        return ref, target


__all__ = ["BrightestStarGuiding"]
