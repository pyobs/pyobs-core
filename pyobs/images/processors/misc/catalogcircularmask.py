import logging
from typing import Any, Tuple, Union, cast

import numpy as np
import numpy.typing as npt
from astropy.table import Table
from pyobs.images.processor import ImageProcessor
from pyobs.images import Image

log = logging.getLogger(__name__)


class CatalogCircularMask(ImageProcessor):
    """
    Filter a source catalog by keeping only entries inside a central circle (or outside it).

    This processor applies a circular spatial filter to the catalog attached
    to a :class:`pyobs.images.Image`. It either retains sources whose positions fall
    within a specified radius of a chosen center, or excludes them if ``exclude_circle``
    is set. Pixel data are not modified; only the image catalog is filtered in place.

    :param float radius: Radius of the circle in pixels used for filtering. Default: required.
    :param tuple[int, int] | tuple[float, float] | tuple[str, str] center:
        Center of the circle. Either a pair of numeric pixel coordinates
        ``(x, y)``, or a pair of FITS header keywords whose values define the center
        (default: ``("CRPIX1", "CRPIX2")``). The center must use the same coordinate
        convention as the catalog (typically FITS 1-based indices in pyobs catalogs).
    :param bool exclude_circle: If ``False``, keep only sources inside the circle.
        If ``True``, exclude sources inside the circle and keep those outside.
        Default: ``False``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - If the image has no catalog (``image.safe_catalog is None``), the image is returned
      unchanged.
    - Determines the circle center:

      - If ``center`` is a pair of strings, reads their values from the FITS header.
      - If ``center`` is numeric, uses those pixel coordinates directly.

    - Builds a boolean mask on the catalog using Euclidean distance in pixel units:

      - Inside selection: ``(x - cx)^2 + (y - cy)^2 <= radius^2``.
      - Outside selection (if ``exclude_circle``): the inequality is reversed.

    - Applies the mask to the catalog and assigns the filtered catalog back to
      ``image.catalog``.
    - Returns the original image object with a filtered catalog; pixel data and header
      are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with a source catalog containing ``x`` and
      ``y`` columns, and optionally header keys for the center if ``center`` is given
      as strings.
    - Output: :class:`pyobs.images.Image` with its catalog filtered by the circular
      criterion. Pixel data are unchanged.

    Configuration (YAML)
    --------------------
    Keep sources within 300 pixels of CRPIX center:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CatalogCircularMask
       radius: 300
       center: ["CRPIX1", "CRPIX2"]
       exclude_circle: false

    Exclude a 100-pixel radius around a specified pixel center:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CatalogCircularMask
       radius: 100
       center: [1024, 1024]
       exclude_circle: true

    Notes
    -----
    - Ensure the center coordinates and catalog positions use the same origin and
      units. Pyobs catalogs often store positions in FITS 1-based convention.
    - ``radius`` is interpreted in pixel units of the catalog/image.
    - The filtering operates solely on the catalog; it does not mask pixels in the
      image data.
    """

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
