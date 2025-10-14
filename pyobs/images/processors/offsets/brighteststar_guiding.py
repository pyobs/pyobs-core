import logging
from typing import Any
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.table import Table, Row
from astropy.wcs import WCS
from pyobs.utils.time import Time
import astropy.units as u

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, AltAzOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestStarGuiding(Offsets):
    """
    Compute guiding offsets by tracking the brightest star relative to an initial reference frame.

    This processor implements a simple auto-guiding strategy based on the
    brightest detected star. On the first call, it initializes a reference position
    from the brightest star in the image catalog and returns without setting offsets.
    On subsequent calls, it finds the current brightest star, computes the pixel offset
    relative to the reference, stores it as PixelOffsets in metadata, and also computes
    the corresponding Alt/Az offsets (in arcseconds) using the image WCS and observer
    location/time. Pixel data and FITS headers are not modified.

    :param tuple[str, str] center_header_cards: Names of FITS header keywords for the
        image center (default: ("CRPIX1", "CRPIX2")). Provided for compatibility; the
        current implementation determines the reference from the brightest star and
        does not use these values directly.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - If the image has no catalog or the catalog is empty, logs a warning and returns
      the image unchanged.
    - Initialization:

      - If no reference is set yet, selects the brightest star by the largest "flux"
        and stores its (x, y) pixel position as the reference. Returns the image.

    - Guiding update:

      - Selects the brightest star in the current catalog and computes pixel offsets
        relative to the stored reference:
          dx = x_current - x_ref, dy = y_current - y_ref
      - Stores PixelOffsets(dx, dy) in the image metadata.
      - Computes Alt/Az offsets:

        - Uses WCS from the FITS header to convert the reference and current star
          pixel positions to sky coordinates (RA/Dec).
        - Builds an observer frame using FITS header location/time:
          LATITUDE [deg], LONGITUD [deg], HEIGHT [m], DATE-OBS.
        - Transforms both positions to AltAz and computes spherical offsets from the
          reference to the current position.
        - Stores AltAzOffsets(dAlt_arcsec, dAz_arcsec) in metadata.

    - Returns the same image object with updated metadata.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with

      - a source catalog containing "x", "y", and "flux" columns,
      - a valid WCS solution in the header (for Alt/Az offsets),
      - site metadata: LATITUDE [deg], LONGITUD [deg], HEIGHT [m],
      - observation time: DATE-OBS.

    - Output: :class:`pyobs.images.Image` with metadata entries set:

      - PixelOffsets(dx, dy) after reference initialization,
      - AltAzOffsets(dAlt_arcsec, dAz_arcsec) likewise.

    Configuration (YAML)
    --------------------
    Initialize guiding on first frame, then report offsets on subsequent frames:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.BrightestStarGuiding
       center_header_cards: ["CRPIX1", "CRPIX2"]  # optional, not used directly

    Notes
    -----
    - Offset sign convention:
      - PixelOffsets are star minus reference (positive dx means the star is to the
        right of the reference; positive dy means above, in the usual image axis sense).
      - AltAzOffsets are returned as (dAlt, dAz) in arcseconds; positive dAlt means
        the target is at higher altitude than the reference; positive dAz means
        larger azimuth (Astropy’s AltAz azimuth increases east of north).
    - Reference management:
      - The first invocation sets the reference star and does not emit offsets.
      - Call reset() to clear the reference and reinitialize on the next image.
    - Catalog coordinates should use the same origin and units consistently across
      images; pyobs catalogs often adopt FITS-like 1-based pixel conventions.
    - Accurate WCS and site/time metadata are required for reliable Alt/Az offsets.
    """

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, center_header_cards: tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        self._center_header_cards = center_header_cards
        self._ref_pos: tuple[float, float] | None = None

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
            self._ref_pos = self._get_brightest_star_position(catalog)
            return image

        star_pos = self._get_brightest_star_position(catalog)

        if self._ref_pos is None:
            raise ValueError("No reference position given.")
        offset = (star_pos[0] - self._ref_pos[0], star_pos[1] - self._ref_pos[1])
        image.set_meta(PixelOffsets(*offset))
        log.info("Found pixel offset of dx=%.2f, dy=%.2f", offset[0], offset[1])

        altaz_offset = self._calc_altaz_offset(image, star_pos)
        image.set_meta(AltAzOffsets(*altaz_offset))
        return image

    def _reference_initialized(self) -> bool:
        return self._ref_pos is not None

    async def reset(self) -> None:
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self._ref_pos = None

    @staticmethod
    def _get_brightest_star_position(catalog: Table) -> tuple[float, float]:
        brightest_star: Row = max(catalog, key=lambda row: row["flux"])
        log.info("Found brightest star at x=%.2f, y=%.2f", brightest_star["x"], brightest_star["y"])
        return brightest_star["x"], brightest_star["y"]

    def _calc_altaz_offset(self, image: Image, star_pos: tuple[float, float]) -> tuple[float, float]:
        radec_ref, radec_target = self._get_radec_ref_target(image, star_pos)
        hdr = image.header
        location = EarthLocation(lat=hdr["LATITUDE"] * u.deg, lon=hdr["LONGITUD"] * u.deg, height=hdr["HEIGHT"] * u.m)
        frame = AltAz(obstime=Time(image.header["DATE-OBS"]), location=location)
        altaz_ref = radec_ref.transform_to(frame)
        altaz_target = radec_target.transform_to(frame)

        # get offset
        daz, dalt = altaz_ref.spherical_offsets_to(altaz_target)

        return dalt.arcsec, daz.arcsec

    def _get_radec_ref_target(self, image: Image, star_pos: tuple[float, float]) -> tuple[SkyCoord, SkyCoord]:
        wcs = WCS(image.header)
        ref = wcs.pixel_to_world(*self._ref_pos)
        target = wcs.pixel_to_world(*star_pos)
        return ref, target


__all__ = ["BrightestStarGuiding"]
