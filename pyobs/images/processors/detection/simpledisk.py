import logging
from typing import Any

import numpy as np
import scipy.ndimage as ndi

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SimpleDisk(ImageProcessor):
    """Simple disc detection in images."""

    __module__ = "pyobs.images.processors.disk"

    def __init__(
        self,
        threshold: int | float = 10.0,
        keyword_x: str = "DISKPOS1",
        keyword_y: str = "DISKPOS2",
        keyword_radius: str = "DISKRAD",
        **kwargs: Any,
    ):
        """Init a new simple disk processor.

        Args:
            threshold: Threshold to determine if a pixel is on the disk.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._threshold = threshold
        self._keyword_x = keyword_x
        self._keyword_y = keyword_y
        self._keyword_radius = keyword_radius

    async def __call__(self, image: Image) -> Image:
        """Detect a disk on image.

        Args:
            image: Image to use.

        Returns:
            Image with new FITS headers.
        """

        data = image.data[0, :, :] if image.is_color else image.data

        # mask according to threshold
        mask = data > self._threshold

        # Keep largest connected component
        lab, nlab = ndi.label(mask)
        if nlab == 0:
            return image
        counts = np.bincount(lab.ravel())
        counts[0] = 0  # background
        k = counts.argmax()
        comp = lab == k

        # Fill holes, then distance transform
        comp = ndi.binary_fill_holes(comp)
        dist = ndi.distance_transform_edt(comp)

        # get max
        y, x = np.unravel_index(np.argmax(dist), dist.shape)
        r = float(dist[y, x])

        # set it
        out = image.copy()
        out.header[self._keyword_y] = y
        out.header[self._keyword_x] = x
        out.header[self._keyword_radius] = r
        return out


__all__ = ["SimpleDisk"]
