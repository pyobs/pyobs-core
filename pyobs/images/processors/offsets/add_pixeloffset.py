import logging
from typing import Tuple, Any

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from .offsets import Offsets

log = logging.getLogger(__name__)


class AddPixelOffset(Offsets):
    """Adds a given pixel offset to the image meta data, so that an acquisition module can apply it."""
    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, pixel_offset_x, pixel_offset_y, **kwargs: Any):
        Offsets.__init__(self, **kwargs)
        self._pixel_offset_x = pixel_offset_x
        self._pixel_offset_y = pixel_offset_y


    async def __call__(self, image: Image) -> Image:
        image.set_meta(PixelOffsets(dx=self._pixel_offset_x, dy=self._pixel_offset_y))
        return image


__all__ = ["AddPixelOffset"]
