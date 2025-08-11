import logging
from typing import Any
import numpy as np

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Normalize(ImageProcessor):
    """Normalize an image to int8 range."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        vmin: float | None = None,
        vmax: float | None = None,
        **kwargs: Any,
    ):
        """Init a new normalize pipeline step.

        Args:
            vmin: Minimum value to normalize.
            vmax: Maximum value to normalize.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._vmin = vmin
        self._vmax = vmax

    async def __call__(self, image: Image) -> Image:
        """Normalize an image.

        Args:
            image: Image to normalize.

        Returns:
            Normalized image.
        """

        vmin = self._vmin
        vmax = self._vmax

        if vmin is None:
            vmin = np.min(image.data)
        if vmax is None:
            vmax = np.max(image.data)

        output_image = image.copy()
        output_image.data = ((output_image.data - vmin) / (vmax - vmin) * 255.0).astype(np.uint8)

        return output_image


__all__ = ["Normalize"]
