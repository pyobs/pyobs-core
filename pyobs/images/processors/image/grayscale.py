import logging
from typing import Any
import numpy as np

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class Grayscale(ImageProcessor):
    """Convert a color image to grayscale."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, r: float = 0.2126, g: float = 0.7152, b: float = 0.0722, **kwargs: Any):
        """Init a new grayscale processor.

        Args:
            r: Weight for red.
            g: Weight for green.
            b: Weight for blue.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._r = r
        self._g = g
        self._b = b

    async def __call__(self, image: Image) -> Image:
        """Convert a color image to grayscale.

        Args:
            image: Image to convert.

        Returns:
            Grayscaled image.
        """

        # 3D, i.e. color, image?
        data = image.data
        if len(data.shape) == 3 and data.shape[0] == 3:
            image.data = (self._r * data[0, :, :] + self._g * data[1, :, :] + self._b * data[2, :, :]).astype(
                np.float32
            )

        return image


__all__ = ["Grayscale"]
