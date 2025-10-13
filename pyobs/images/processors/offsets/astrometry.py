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
    """
    Compute pixel offsets from WCS by comparing image reference coordinates to telescope pointing.

    This asynchronous processor requires a valid WCS in the FITS header (run an
    astrometry solver beforehand). It reads two sky-coordinate pairs from the header:
    the image/WCS reference sky position (CRVAL1/CRVAL2) and the telescope’s current
    sky position (TEL-RA/TEL-DEC), converts both to pixel coordinates using the WCS,
    and computes their difference. The resulting pixel offset
    dx = x_tel - x_ref, dy = y_tel - y_ref is stored in the image metadata as a
    PixelOffsets object. It also stores the on-sky angular separation between the two
    positions (OnSkyDistance). Pixel data and standard headers are not modified.

    Prerequisite: must run after an astrometry processor so that the FITS header
    contains a valid WCS solution.

    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Copies the input image and constructs a :class:`astropy.wcs.WCS` from its header.
    - Reads sky coordinates (in degrees, ICRS frame):
      - Reference: CRVAL1/CRVAL2 (the WCS reference world coordinates).
      - Telescope: TEL-RA/TEL-DEC (the telescope pointing).
    - Converts both sky positions to pixel coordinates via WCS.world_to_pixel.
    - Computes pixel offsets:
      - dx = x_telescope - x_reference
      - dy = y_telescope - y_reference
    - Computes on-sky angular distance between the two sky positions.
    - Stores results in image metadata:
      - PixelOffsets(dx, dy)
      - OnSkyDistance(angle)
    - Returns the modified copy of the image; pixel data and FITS headers are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with a valid WCS in the header and the
      keywords CRVAL1, CRVAL2, TEL-RA, TEL-DEC present (in degrees, ICRS).
    - Output: :class:`pyobs.images.Image` (copied) with metadata entries for
      PixelOffsets and OnSkyDistance set.

    Configuration (YAML)
    --------------------
    Run after astrometric calibration to attach pixel offsets:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.AstrometryOffsets

    Notes
    -----
    - Sign convention: positive dx means the telescope pointing is at a larger x pixel
      coordinate than the WCS reference position; positive dy likewise for y.
      Ensure this convention matches the downstream module that applies the offsets.
    - For typical WCS, the CRVAL position maps near the CRPIX pixel; thus the offset
      is approximately the difference between the telescope pointing and the WCS
      reference pixel location.
    - TEL-RA/TEL-DEC must be in ICRS degrees; adjust or convert if your system uses a
      different frame or units.
    """

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
            self._image.header[header_cards[1]] * u.deg,  # type: ignore
            frame="icrs",
        )

        pixel_coordinates = self._wcs.world_to_pixel(coordinates)  # type: ignore
        return coordinates, pixel_coordinates


__all__ = ["AstrometryOffsets"]
