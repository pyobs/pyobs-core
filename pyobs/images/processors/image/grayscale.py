import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class Grayscale(ImageProcessor):
    """
    Convert a color image to grayscale using weighted RGB channels.

    This processor converts a 3-channel color :class:`pyobs.images.Image`
    to grayscale by forming a weighted linear combination of the red, green, and blue
    channels:

    ``gray = r * R + g * G + b * B``

    By default, the weights ``r=0.2126``, ``g=0.7152``, and ``b=0.0722`` correspond to the
    ITU-R BT.709 (Rec. 709) luma coefficients. The conversion is delegated to
    :meth:`pyobs.images.Image.to_grayscale`.

    :param float r: Weight for the red channel. Default: ``0.2126``.
    :param float g: Weight for the green channel. Default: ``0.7152``.
    :param float b: Weight for the blue channel. Default: ``0.0722``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Calls :meth:`pyobs.images.Image.to_grayscale(r, g, b)` on the input image and returns
      the resulting image.
    - The weights need not sum to 1.0; they are used as provided for a linear combination.
    - Header metadata are preserved by the underlying conversion method.
    - Typical input layout for color images is channel-first ``(C, H, W)`` with ``C=3`` (RGB).

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` (color image with 3 channels).
    - Output: :class:`pyobs.images.Image` (single-channel grayscale image, shape dependent
      on the implementation of :meth:`to_grayscale`).

    Configuration (YAML)
    --------------------
    Default Rec. 709 weights:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Grayscale
       # r: 0.2126
       # g: 0.7152
       # b: 0.0722

    Custom weights:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Grayscale
       r: 0.3
       g: 0.59
       b: 0.11

    Notes
    -----
    - Ensure the input image is a 3-channel color image; otherwise the underlying
      conversion may be a no-op or raise an error, depending on implementation.
    - The default weights correspond to BT.709 luma; other choices (e.g., BT.601)
      may be preferable depending on your imaging pipeline.
    """

    __module__ = "pyobs.images.processors.image"

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
        return image.to_grayscale(self._r, self._g, self._b)


__all__ = ["Grayscale"]
