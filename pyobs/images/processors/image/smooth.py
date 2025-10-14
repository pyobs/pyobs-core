import logging
from typing import Any, Literal

import scipy.ndimage

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)


class Smooth(ImageProcessor):
    """
    Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter.

    This processor applies a Gaussian filter to the pixel data of a
    :class:`pyobs.images.Image` to reduce noise or gently blur features. The operation
    is performed with :func:`scipy.ndimage.gaussian_filter` and affects all axes of the
    image array.

    :param float sigma: Standard deviation of the Gaussian kernel (in pixels). Larger values
                        produce stronger smoothing. Required.
    :param int order: The order of the filter along each axis (``0`` for smoothing; higher
                      values compute derivatives of the Gaussian). Default: ``0``.
    :param {"reflect","constant","nearest","mirror","wrap","grid-constant","grid-mirror","grid-wrap"} mode:
        How the input array is extended at borders. See SciPy’s documentation for details.
        Default: ``"reflect"``.
    :param float cval: Constant value used to fill beyond edges when ``mode="constant"``.
                       Default: ``0.0``.
    :param float truncate: Truncate the filter at this many standard deviations. Values beyond
                           ``truncate * sigma`` are ignored. Default: ``4.0``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Creates a copy of the input image. If no data are present (``safe_data is None``),
      logs a warning and returns the original image unchanged.
    - Applies :func:`scipy.ndimage.gaussian_filter` to ``output_image.data`` with the configured
      parameters.
    - For 2D images (``H, W``), smoothing is applied over both spatial axes.
    - For 3D arrays (e.g., channel-first ``C, H, W``), smoothing is applied over all axes,
      including the channel axis. This mixes channels; if this is not desired, consider
      processing each channel separately upstream.
    - Header metadata are preserved; only the pixel data are modified.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with Gaussian-smoothed data.

    Configuration (YAML)
    --------------------
    Basic smoothing:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Smooth
       sigma: 1.5

    Edge handling with constant padding:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Smooth
       sigma: 2.0
       mode: "constant"
       cval: 0.0

    Derivative of Gaussian (edge detection-like):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Smooth
       sigma: 1.0
       order: 1

    Notes
    -----
    - Dtype considerations: SciPy performs filtering in floating point and may cast the result
      back to the input dtype. If the input is integer-typed, fractional values will be rounded;
      for best results, use floating-point image data.
    - The ``order`` parameter controls derivatives of the Gaussian; ``order=0`` performs
      standard smoothing, while ``order>0`` computes Gaussian derivatives and may enhance edges.
    - For multi-channel images where you do not want cross-channel blurring, split channels and
      smooth each channel independently before recombining.

    See also
    --------
    SciPy reference for :func:`scipy.ndimage.gaussian_filter`:
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html#scipy-ndimage-gaussian-filter
    """

    __module__ = "pyobs.images.processors.image"

    def __init__(
        self,
        sigma: float,
        order: int = 0,
        mode: Literal[
            "reflect", "constant", "nearest", "mirror", "wrap", "grid-constant", "grid-mirror", "grid-wrap"
        ] = "reflect",
        cval: float = 0.0,
        truncate: float = 4.0,
        **kwargs: Any,
    ):
        """Init a new smoothing pipeline step.

        Args:
            sigma: Standard deviation for Gaussian kernel.
            order: The order of the filter along each axis.
            mode: Determines how the input array is extended when the filter overlaps a border.
            cval: Value to fill past edges of input if mode is ‘constant’.
            truncate: Truncate the filter at this many standard deviations.

        See Also: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html#scipy-ndimage-gaussian-filter
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.sigma = sigma
        self.order = order
        self.mode = mode
        self.cval = cval
        self.truncate = truncate

    async def __call__(self, image: Image) -> Image:
        """Smooth an image.

        Args:
            image: Image to smooth.

        Returns:
            Smoothed image.
        """

        output_image = image.copy()
        if output_image.safe_data is None:
            log.warning("No data found in image.")
            return image

        output_image.data = scipy.ndimage.gaussian_filter(
            output_image.data, self.sigma, order=self.order, mode=self.mode, cval=self.cval, truncate=self.truncate
        )

        return output_image


__all__ = ["Smooth"]
