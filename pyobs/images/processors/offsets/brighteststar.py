import logging
from typing import Tuple, Any

from astropy.coordinates import Angle
from astropy.table import Table, Row
from astropy.wcs import WCS

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestStarOffsets(Offsets):
    """
    Compute pixel offsets from the image center to the brightest star and store them in metadata.

    This processor reads the image center from FITS header keywords
    (default CRPIX1/CRPIX2), finds the brightest star in the attached source catalog
    (by maximum flux), computes the pixel offset between the center and that star,
    and stores the result as a PixelOffsets metadata entry. It also computes the
    on-sky angular separation between the two positions using the image WCS and
    stores it as OnSkyDistance. Pixel data and standard headers are not modified.

    :param tuple[str, str] center_header_cards: Names of the FITS header keywords
        that give the x and y pixel coordinates of the image center
        (default: ("CRPIX1", "CRPIX2")).
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - If the image has no catalog or the catalog is empty, logs a warning and returns
      the image unchanged.
    - Selects the brightest star as the catalog row with the largest "flux" value
      and reads its "x" and "y" pixel coordinates.
    - Reads the image center pixel coordinates from the specified header keywords.
    - Computes pixel offsets:

      - dx = x_star - x_center
      - dy = y_star - y_center

    - Uses WCS from the image header to convert both positions to sky coordinates and
      computes their angular separation.
    - Stores results in image metadata:

      - PixelOffsets(dx, dy)
      - OnSkyDistance(angle)

    - Returns the same image object with updated metadata.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with:

      - a source catalog containing "x", "y", and "flux" columns
      - FITS header keys for the center (e.g., CRPIX1/CRPIX2)
      - a valid WCS solution in the header for sky separation

    - Output: :class:`pyobs.images.Image` with PixelOffsets and OnSkyDistance set in metadata.

    Configuration (YAML)
    --------------------
    Use CRPIX center:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.BrightestStarOffsets

    Use custom center keywords:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.BrightestStarOffsets
       center_header_cards: ["CX", "CY"]

    Notes
    -----
    - The sign convention for offsets is star minus center:
      positive dx means the star lies to the right of the center, positive dy means
      it lies above the center, assuming standard image axes.
    - Ensure catalog coordinates and center header values use the same pixel origin
      and units (pyobs catalogs often use FITS-like 1-based coordinates).
    - A valid WCS in the header is required to compute on-sky separation.
    """

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, center_header_cards: Tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        self._center_header_cards = center_header_cards

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

        star_pos = self._get_brightest_star_position(catalog)
        center = image.header[self._center_header_cards[0]], image.header[self._center_header_cards[1]]

        offset = (star_pos[0] - center[0], star_pos[1] - center[1])
        on_sky_distance = self._calc_on_sky_distance(image, center, star_pos)

        image.set_meta(PixelOffsets(*offset))
        image.set_meta(OnSkyDistance(on_sky_distance))
        return image

    @staticmethod
    def _get_brightest_star_position(catalog: Table) -> Tuple[float, float]:
        brightest_star: Row = max(catalog, key=lambda row: row["flux"])
        return brightest_star["x"], brightest_star["y"]

    @staticmethod
    def _calc_on_sky_distance(image: Image, center: Tuple[float, float], star_pos: Tuple[float, float]) -> Angle:
        wcs = WCS(image.header)
        center_coordinates = wcs.pixel_to_world(*center)
        star_coordinates = wcs.pixel_to_world(*star_pos)

        return center_coordinates.separation(star_coordinates)


__all__ = ["BrightestStarOffsets"]
