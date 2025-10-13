import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SolarHelioprojective(ImageProcessor):
    """Add solar helioprojective WCS to image."""

    __module__ = "pyobs.images.processors.wcs"

    def __init__(
        self,
        keyword_x: str = "DISKPOS1",
        keyword_y: str = "DISKPOS2",
        keyword_radius: str = "DISKRAD",
        **kwargs: Any,
    ):
        """Init a new helioprojective wcs processor.

        Args:
            keyword_x: X coordinate of sun in image.
            keyword_y: Y coordinate of sun in image.
            keyword_radius: Radius of sun in image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._keyword_x = keyword_x
        self._keyword_y = keyword_y
        self._keyword_radius = keyword_radius

    async def __call__(self, image: Image) -> Image:
        """Add WCS.

        Args:
            image: Image to use.

        Returns:
            Image with new WCS.
        """
        import sunpy.coordinates  # type: ignore

        cdelt = sunpy.coordinates.sun.angular_radius().degree / 470.0

        out = image.copy()
        out.header["CRPIX1"] = image.header[self._keyword_x]
        out.header["CRPIX2"] = image.header[self._keyword_y]
        out.header["CRVAL1"] = 0.0
        out.header["CRVAL2"] = 0.0
        out.header["CTYPE1"] = "HPLN-TAN"
        out.header["CTYPE2"] = "HPLT-TAN"
        out.header["CDELT1"] = cdelt
        out.header["CDELT2"] = cdelt
        return out


__all__ = ["SolarHelioprojective"]
