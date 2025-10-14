import logging
from typing import Any, Tuple

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors._daobackgroundremover import _DaoBackgroundRemover

log = logging.getLogger(__name__)


class RemoveBackground(ImageProcessor):
    """
    Estimate and subtract the background from an image using a DAOPhot-style method.

    This processor applies robust background estimation and removes it
    from the image, producing a background-corrected result. The background is
    estimated on a grid with sigma-clipping and optional smoothing, then subtracted
    from the pixel data. The implementation delegates to
    :class:`pyobs.images.processors.detection._DaoBackgroundRemover`.

    :param float sigma: Sigma for kappa–sigma clipping used in background estimation.
                        Default: ``3.0``.
    :param tuple[int, int] box_size: Size of the grid boxes (ny, nx) in pixels over
                                     which the background is estimated. Default: ``(50, 50)``.
    :param tuple[int, int] filter_size: Size (ny, nx) of the smoothing filter applied
                                        to the coarse background map. Default: ``(3, 3)``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Builds a background model using kappa–sigma clipping within tiles of size
      ``box_size`` and smooths the model with a filter of size ``filter_size``.
    - Subtracts the estimated background from the image data.
    - Returns the background-corrected image; header and catalog are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with 2D pixel data.
    - Output: :class:`pyobs.images.Image` with background subtracted from its pixel data.

    Configuration (YAML)
    --------------------
    Basic background removal:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.RemoveBackground
       sigma: 3.0
       box_size: [50, 50]
       filter_size: [3, 3]

    Notes
    -----
    - Choose ``box_size`` large enough to capture slowly varying background while
      avoiding contamination by extended sources.
    - Increasing ``sigma`` reduces the influence of outliers on the background estimate.
    - If your image contains strong gradients or large-scale structures, consider
      tuning ``box_size`` and ``filter_size`` to avoid over-subtraction.
    """

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        sigma: float = 3.0,
        box_size: Tuple[int, int] = (50, 50),
        filter_size: Tuple[int, int] = (3, 3),
        **kwargs: Any,
    ):
        """Init an image processor that removes background from image.

        Args:
            sigma: Sigma for clipping
            box_size: Box size for bkg estimation.
            filter_size: Size of filter.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._background_remover = _DaoBackgroundRemover(sigma, box_size, filter_size)

    async def __call__(self, image: Image) -> Image:
        """Remove background from image.

        Args:
            image: Image to remove background from.

        Returns:
            Image without background.
        """

        return self._background_remover(image)


__all__ = ["RemoveBackground"]
