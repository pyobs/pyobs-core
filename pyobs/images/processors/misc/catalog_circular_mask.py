import logging
from typing import Any, Tuple, Union

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image

log = logging.getLogger(__name__)


class CatalogCircularMask(ImageProcessor):
    """Mask catalog for central circle with given radius."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        radius: float,
        center: Union[Tuple[int, int], Tuple[float, float], Tuple[str, str]] = ("CRPIX1", "CRPIX2"),
        **kwargs: Any,
    ):
        """Init an image processor that masks out everything except for a central circle.

        Args:
            radius: radius of the central circle in pixels
            center: fits-header keywords or pixel coordinates defining the center of the circle
        """
        ImageProcessor.__init__(self, **kwargs)

        # init
        self._radius = radius
        self._radius_is_corrected = False
        self._center = center

    async def __call__(self, image: Image) -> Image:
        """Remove everything outside the given radius from the image.

        Args:
            image: Image to mask.

        Returns:
            Image with masked Catalog.
        """
        if not self._radius_is_corrected:
            self._correct_radius_for_binning(image)

        center_x, center_y = self._get_center(image)

        catalog = image.safe_catalog
        mask = (catalog["x"] - center_x) ** 2 + (catalog["y"] - center_y) ** 2 <= self._radius**2
        image.catalog = catalog[mask]

        return image

    def _correct_radius_for_binning(self, image):
        binning_x, binning_y = image.header["XBINNING"], image.header["YBINNING"]
        if binning_x == binning_y:
            self._radius /= binning_x
        else:
            log.warning("Binning factor is not the same for x and y axis. Filter radius remains uncorrected ...")
        self._radius_is_corrected = True

    def _get_center(self, image):
        if isinstance(self._center[0], str) and isinstance(self._center[1], str):
            return image.header[self._center[0]], image.header[self._center[1]]
        else:
            return self._center


__all__ = ["CatalogCircularMask"]
