import logging
from typing import Any

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class AddPixelOffset(Offsets):
    """
    Attach desired pixel offsets to the image metadata for later application by an acquisition module.

    This processor stores a pixel-offset request in the image metadata as
    a :class:`pyobs.images.processors.offsets.PixelOffsets` object. Downstream modules
    (e.g., acquisition/guiding) can read these offsets and apply the corresponding
    pointing shift. Pixel data and FITS headers are not modified.

    :param float pixel_offset_x: Requested offset in pixels along the image x-axis (columns).
    :param float pixel_offset_y: Requested offset in pixels along the image y-axis (rows).
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Creates a :class:`PixelOffsets` instance with the given ``dx`` and ``dy`` values.
    - Calls ``image.set_meta(...)`` to attach the offsets to the image metadata.
    - Returns the same image object; pixel data and FITS headers remain unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`.
    - Output: :class:`pyobs.images.Image` with a ``PixelOffsets`` metadata entry set.

    Configuration (YAML)
    --------------------
    Request a shift of +12 pixels in x and -8 pixels in y:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.AddPixelOffset
       pixel_offset_x: 12.0
       pixel_offset_y: -8.0

    Notes
    -----
    - Offsets are stored as metadata only; applying them is the responsibility of a
      downstream acquisition or control module that understands ``PixelOffsets``.
    - Coordinate conventions (sign and axis direction) must match those expected by
      the module that consumes these offsets.
    """

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, pixel_offset_x: float, pixel_offset_y: float, **kwargs: Any):
        Offsets.__init__(self, **kwargs)
        self._pixel_offset_x = pixel_offset_x
        self._pixel_offset_y = pixel_offset_y

    async def __call__(self, image: Image) -> Image:
        image.set_meta(PixelOffsets(dx=self._pixel_offset_x, dy=self._pixel_offset_y))
        return image


__all__ = ["AddPixelOffset"]
