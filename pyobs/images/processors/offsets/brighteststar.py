import logging
from typing import Tuple, Any

from astropy.coordinates import Angle
from astropy.table import Table
from astropy.wcs import WCS

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from .offsets import Offsets

log = logging.getLogger(__name__)


class BrightestStarOffsets(Offsets):
    """Calculates offsets from the center of the image to the brightest star."""

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
        catalog_copy = catalog.copy()
        catalog_copy.sort("flux", reverse=True)

        return catalog_copy["x"][0], catalog_copy["y"][0]

    @staticmethod
    def _calc_on_sky_distance(image: Image, center: Tuple[float, float], star_pos: Tuple[float, float]) -> Angle:
        wcs = WCS(image.header)
        center_coordinates = wcs.pixel_to_world(*center)
        star_coordinates = wcs.pixel_to_world(*star_pos)

        return center_coordinates.separation(star_coordinates)


__all__ = ["BrightestStarOffsets"]
