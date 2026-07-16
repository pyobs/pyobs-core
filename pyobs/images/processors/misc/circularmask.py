from __future__ import annotations

import logging
from typing import Any

import numpy as np

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class CircularMask(ImageProcessor):
    """
    Mask an image by keeping only pixels inside a central circle of a given radius.

    This processor reads the circle center from two FITS header keywords
    (e.g., CRPIX1/CRPIX2) and constructs a circular mask in pixel coordinates. Pixels
    outside the circle are flagged in ``image.mask``; pixel data are left untouched. Any
    pre-existing mask on the image is combined (logical OR) with the new one rather than
    being overwritten.

    :param float radius: Radius of the circular pass region in pixels. Pixels with
                         squared distance to the center less than or equal to
                         ``radius**2`` are kept.
    :param tuple[str, str] center: Names of the FITS header keywords whose values
                                   give the x and y pixel coordinates of the circle
                                   center (default: ``("CRPIX1", "CRPIX2")``).
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Reads the circle center from ``image.header[center[0]]`` and
      ``image.header[center[1]]``.
    - Builds a boolean mask on the 2D pixel grid that is ``True`` outside the circle
      and ``False`` inside it (boundary inclusive), and assigns it to a copy of the
      image's ``mask``. If the image already has a mask, the new mask is combined with
      it via logical OR instead of replacing it.
    - Returns a copy of the image with the updated mask; pixel data, header, and
      catalog are not changed.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with 2D pixel data and FITS header containing
      the specified center keywords.
    - Output: :class:`pyobs.images.Image` (copied) with pixels outside the circle
      marked in ``mask``; pixel data are unchanged.

    Configuration (YAML)
    --------------------
    Keep only pixels within a 500-pixel radius around CRPIX:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CircularMask
       radius: 500
       center: ["CRPIX1", "CRPIX2"]

    Use custom center keywords:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CircularMask
       radius: 250
       center: ["CX", "CY"]

    Notes
    -----
    - The center values must use the same pixel coordinate convention as the mask
      grid. FITS CRPIX values are typically 1-based; if your image indices are 0-based,
      ensure consistency to avoid off-by-one shifts.
    - The implementation operates on 2D images. Multi-plane/color images are not
      supported by this processor as written.
    """

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, radius: float, center: tuple[str, str] = ("CRPIX1", "CRPIX2"), **kwargs: Any):
        """Init an image processor that masks out everything except for a central circle.

        Args:
            radius: radius of the central circle in pixels
            center: fits-header keywords defining the pixel coordinates of the center of the circle
        """
        ImageProcessor.__init__(self, **kwargs)

        # init
        self._center = center
        self._radius = radius

    async def __call__(self, image: Image) -> Image:
        """Mask everything outside the given radius from the image.

        Args:
            image: Image to mask.

        Returns:
            Image with pixels outside the circle marked in its mask.
        """

        center_x, center_y = image.header[self._center[0]], image.header[self._center[1]]

        nx, ny = image.data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)

        outside_circle = (x_coordinates - center_x) ** 2 + (y_coordinates - center_y) ** 2 > self._radius**2
        outside_circle = outside_circle.transpose()

        output_image = image.copy()
        if output_image.safe_mask is not None:
            output_image.mask = np.logical_or(output_image.mask, outside_circle)
        else:
            output_image.mask = outside_circle

        return output_image


__all__ = ["CircularMask"]
