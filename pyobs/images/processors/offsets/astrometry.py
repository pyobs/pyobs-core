import logging
from typing import Any, Tuple, Optional
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from . import Offsets

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class AstrometryOffsets(Offsets):
    """An offset-calculation method based on astrometry. Returns offset to real coordinates."""

    def __init__(self, **kwargs: Any):
        """Initializes new astrometry offsets.

        MUST run after an astrometry processor.
        """
        Offsets.__init__(self, **kwargs)

        self._image: Optional[Image] = None
        self._wcs: Optional[WCS] = None

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        self._image = image.copy()
        self._wcs = WCS(image.header)

        center_sky_coord, center_pixel_coord = self._get_coordinates_from_header(("CRVAL1", "CRVAL2"))
        teleskope_sky_coord, telescope_pixel_coord = self._get_coordinates_from_header(("TEL-RA", "TEL-DEC"))

        offset = telescope_pixel_coord[0] - center_pixel_coord[0], telescope_pixel_coord[1] - center_pixel_coord[1]
        on_sky_distance = center_sky_coord.separation(teleskope_sky_coord)

        self._image.set_meta(PixelOffsets(*offset))
        self._image.set_meta(OnSkyDistance(on_sky_distance))
        return self._image

    def _get_coordinates_from_header(self, header_cards: Tuple[str, str]) -> Tuple[SkyCoord, Tuple[float, float]]:
        coordinates = SkyCoord(
            self._image.header[header_cards[0]] * u.deg,  # type: ignore
            self._image.header[header_cards[1]] * u.deg,    # type: ignore
            frame="icrs")

        pixel_coordinates = self._wcs.world_to_pixel(coordinates)   # type: ignore
        return coordinates, pixel_coordinates


__all__ = ["AstrometryOffsets"]
