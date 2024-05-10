import logging
from typing import Tuple, Any, Optional

from astropy.coordinates import Angle
from astropy.table import Table, Row
from astropy.wcs import WCS
from pandas._typing import npt

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
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
        on_sky_distance = self._calc_on_sky_distance(image, self._ref_pos, star_pos)

        image.set_meta(PixelOffsets(*offset))
        image.set_meta(OnSkyDistance(on_sky_distance))
        return image

    def _reference_initialized(self):
        return self._ref_image is not None

    @staticmethod
    def _get_brightest_star_position(catalog: Table) -> Tuple[float, float]:
        brightest_star: Row = max(catalog, key=lambda row: row["flux"])
        return brightest_star["x"], brightest_star["y"]

    @staticmethod
    def _calc_on_sky_distance(image: Image, ref_pos: Tuple[float, float], star_pos: Tuple[float, float]) -> Angle:
        wcs = WCS(image.header)
        reference_coordinates = wcs.pixel_to_world(*ref_pos)
        star_coordinates = wcs.pixel_to_world(*star_pos)

        return reference_coordinates.separation(star_coordinates)


__all__ = ["BrightestStarGuiding"]
