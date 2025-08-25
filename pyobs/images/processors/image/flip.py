import logging
from typing import Any
import numpy as np

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Flip(ImageProcessor):
    """flip an image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        flip_x: bool = False,
        flip_y: bool = False,
        **kwargs: Any,
    ):
        """Init a new flip pipeline step.

        Args:
            flip_x: If True, flip the image horizontally.
            flip_y: If True, flip the image vertically.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.flip_x = flip_x
        self.flip_y = flip_y

    async def __call__(self, image: Image) -> Image:
        """Flip an image.

        Args:
            image: Image to flip.

        Returns:
            Flipped image.
        """

        output_image = image.copy()
        if output_image.safe_data is None:
            log.warning("No data found in image.")
            return image

        # do we have three dimensions in array? need this for deciding which axis to flip
        is_3d = len(output_image.data.shape) == 3

        if self.flip_x:
            output_image.data = np.flip(output_image.data, axis=1 if is_3d else 0)
        if self.flip_y:
            output_image.data = np.flip(output_image.data, axis=2 if is_3d else 1)

        return output_image


__all__ = ["Flip"]
