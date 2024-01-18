import logging
from typing import Tuple, Any
import numpy as np

from pyobs.images import Image
from . import Offsets
from ...meta.genericoffset import GenericOffset

log = logging.getLogger(__name__)


class FitsHeaderOffsets(Offsets):
    """An offset-calculation method based on fits headers."""

    def __init__(self, target: Tuple[str, str], center: Tuple[str, str] = ("DET-CPX1", "DET-CPX2"), **kwargs: Any):
        """Initializes new fits header offsets."""
        Offsets.__init__(self, **kwargs)

        if len(target) != 2 or len(center) != 2:
            raise ValueError("Target and center must be of length 2!")

        self.center = center
        self.target = target

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        target = [image.header[x] for x in self.target]
        center = [image.header[x] for x in self.center]

        offset = np.subtract(target, center)

        output_image = image.copy()
        output_image.set_meta(GenericOffset(*offset))
        return output_image


__all__ = ["FitsHeaderOffsets"]
