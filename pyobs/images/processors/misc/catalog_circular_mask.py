import logging
from typing import Any, Tuple, Union, cast

import numpy as np
import numpy.typing as npt
from astropy.table import Table
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
        exclude_circle: bool = False,
        **kwargs: Any,
    ):
        """Init an image processor that masks out everything except for a central circle.

        Args:
            radius: radius of the central circle in pixels
            center: fits-header keywords or pixel coordinates defining the center of the circle
            exclude_circle: whether to exclude the central circle from the catalog
        """
        ImageProcessor.__init__(self, **kwargs)

        self._radius = radius
        self._center = center
        self._exclude_circle = exclude_circle

    async def __call__(self, image: Image) -> Image:
        """Remove everything outside the given radius from the image.

        Args:
            image: Image to mask.

        Returns:
            Image with masked Catalog.
        """

        catalog = image.safe_catalog
        if catalog is not None:
            mask = self._get_mask(image, catalog)
            image.catalog = catalog[mask]

        return image

    def _get_mask(self, image: Image, catalog: Table) -> npt.NDArray[np.bool]:
        center_x, center_y = self._get_center(image)
        # TODO: what??
        if self._exclude_circle:
            mask = (catalog["x"] - center_x) ** 2 + (catalog["y"] - center_y) ** 2 >= self._radius**2
        else:
            mask = (catalog["x"] - center_x) ** 2 + (catalog["y"] - center_y) ** 2 <= self._radius**2
        return cast(npt.NDArray[np.bool], mask)

    def _get_center(self, image: Image) -> tuple[float, float]:
        if isinstance(self._center[0], str) and isinstance(self._center[1], str):
            return image.header[self._center[0]], image.header[self._center[1]]
        else:
            return self._center


__all__ = ["CatalogCircularMask"]
