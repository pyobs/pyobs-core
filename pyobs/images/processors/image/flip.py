import logging
from typing import Any
import numpy as np

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Flip(ImageProcessor):
    """
    Flip image pixels horizontally (x-axis) and/or vertically (y-axis).

    This processor flips the pixel data of a pyobs :class:`pyobs.images.Image` along the
    horizontal (left–right) and/or vertical (top–bottom) axes. It is typically used to
    correct camera orientation or mirror inversions so that subsequent processing and
    display match the desired coordinate convention.

    :param bool flip_x: If ``True``, flip the image left–right (along the x-axis).
                        Default: ``False``.
    :param bool flip_y: If ``True``, flip the image top–bottom (along the y-axis).
                        Default: ``False``.

    .. note::
       - If both ``flip_x`` and ``flip_y`` are ``True``, the result is equivalent to a 180° rotation.
       - If both are ``False``, this processor performs no operation (no-op).
       - Pixel coordinates transform as:
         ``x -> (width - 1 - x)`` when ``flip_x`` is ``True`` and
         ``y -> (height - 1 - y)`` when ``flip_y`` is ``True``.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` with pixel data flipped according to the configured axes.
      The output image has the same shape and dtype as the input. Header metadata (including WCS)
      are preserved and not modified by this processor; workflows relying on orientation-sensitive
      metadata may need to update them downstream.

    Configuration (YAML)
    --------------------
    Instantiate and configure via YAML, for example:

    .. code-block:: yaml

       class: pyobs.images.processors.image.flip.Flip
       flip_x: true
       flip_y: false

    Examples
    --------
    - Correct a mirror inversion by flipping horizontally:

      .. code-block:: yaml

         class: pyobs.images.processors.image.flip.Flip
         flip_x: true

    - Flip vertically to match an optical path or mount orientation:

      .. code-block:: yaml

         class: pyobs.images.processors.image.flip.Flip
         flip_y: true
    """

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
