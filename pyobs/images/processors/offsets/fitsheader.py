import logging
from typing import Tuple, Any
import numpy as np

from pyobs.images import Image
from . import Offsets
from ...meta.genericoffset import GenericOffset

log = logging.getLogger(__name__)


class FitsHeaderOffsets(Offsets):
    """
    Compute a 2D offset from FITS header coordinates and store it in image metadata.

    This processor reads two pairs of FITS header keywords representing a
    target position and a reference (center) position, computes the component-wise
    difference target − center, and stores the result as a GenericOffset metadata
    entry on a copy of the image. Pixel data and standard headers are not modified.

    :param tuple[str, str] target: Names of the FITS header keywords for the target
        coordinates (e.g., measured or desired position), given as (x_key, y_key).
        Required.
    :param tuple[str, str] center: Names of the FITS header keywords for the reference
        (center) coordinates, given as (x_key, y_key). Default: ("DET-CPX1", "DET-CPX2").
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Validates at initialization that both ``target`` and ``center`` are 2-tuples.
    - On call:
      - Reads the target and center values from the image header.
      - Computes the offset as (target_x − center_x, target_y − center_y).
      - Creates a copy of the input image and attaches the result as
        ``GenericOffset(dx, dy)`` in the image metadata.
      - Returns the modified copy; pixel data and header values are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with FITS header containing the specified
      target and center keywords, whose values are numeric.
    - Output: :class:`pyobs.images.Image` (copied) with a ``GenericOffset`` metadata
      entry set to the computed (dx, dy).

    Configuration (YAML)
    --------------------
    Use default center keys and custom target keys:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.FitsHeaderOffsets
       target: ["OBJX", "OBJY"]

    Custom center and target keys:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.FitsHeaderOffsets
       target: ["TEL-CPX1", "TEL-CPX2"]
       center: ["CRPIX1", "CRPIX2"]

    Notes
    -----
    - Units and origin are inherited from the header values (typically pixels). The
      sign convention is target minus center:
      dx = target_x − center_x, dy = target_y − center_y.
    - Ensure the target and center coordinates use the same convention (e.g., both
      0-based or both FITS-like 1-based) to avoid off-by-one errors.
    - ``GenericOffset`` is a unit-agnostic offset container; downstream consumers must
      interpret the units appropriately.
    """

    __module__ = "pyobs.images.processors.offsets"

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
