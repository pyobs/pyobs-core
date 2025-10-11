import logging
from typing import Any
import numpy as np

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Normalize(ImageProcessor):
    """
    Normalize image pixel values to the 8-bit range [0, 255].

    This asynchronous processor linearly rescales the input image data to ``uint8`` using
    user-specified or automatically determined bounds:

    ``normalized = ((data - vmin) / (vmax - vmin) * 255).astype(uint8)``

    If ``vmin`` or ``vmax`` are not provided, they are computed from the image data via
    ``numpy.min`` and ``numpy.max`` across the entire array.

    :param float vmin: Minimum value to normalize from. If ``None``, uses ``np.min(image.data)``.
                       Default: ``None``.
    :param float vmax: Maximum value to normalize to. If ``None``, uses ``np.max(image.data)``.
                       Default: ``None``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Creates a copy of the input image and replaces its ``data`` with a normalized
      ``numpy.uint8`` array.
    - If ``vmin``/``vmax`` are ``None``, they are computed over the entire array
      (all channels and pixels).
    - The normalization is applied element-wise to the entire array; for multi-channel
      images (e.g., channel-first ``(C, H, W)``), a single global ``vmin``/``vmax``
      is used for all channels (no per-channel normalization).
    - Header metadata are preserved; only the pixel data and dtype change.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with data normalized to ``uint8``.

    Configuration (YAML)
    --------------------
    Automatic bounds:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Normalize
       # vmin: null
       # vmax: null

    Explicit bounds (e.g., for 16-bit images):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Normalize
       vmin: 0
       vmax: 65535

    Notes
    -----
    - Precision loss: Converting to 8-bit discards dynamic range; use only when appropriate
      for visualization or downstream tools that require ``uint8``.
    - Division by zero: If ``vmin == vmax``, normalization is undefined and will result
      in NaNs/Infs before casting; consider guarding against identical bounds upstream.
    - Out-of-range values: If you specify ``vmin``/``vmax`` that do not bracket the data,
      values below/above the range will map outside [0, 255]; when cast to ``uint8``,
      such values wrap modulo 256 rather than clip. If clipping is desired, pre-clip
      the data or choose bounds based on the data range.
    - NaNs: If the data contain NaNs, ``np.min``/``np.max`` will propagate NaNs to
      the bounds, producing NaNs in the normalized array. Clean or mask NaNs beforehand
      if necessary.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

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
