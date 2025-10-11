import logging
from typing import Any, cast
import numpy as np
import numpy.typing as npt

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SoftBin(ImageProcessor):
    """
    Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS headers.

    This asynchronous processor performs software binning on a 2D :class:`pyobs.images.Image`
    by partitioning the array into ``binning × binning`` blocks and replacing each block with
    its arithmetic mean. The result is a downsampled image of shape ``(H // binning, W // binning)``.
    After binning, common FITS/WCS header keywords are updated to reflect the new pixel grid.

    :param int binning: The binning factor (block size in pixels along each axis). Default: ``2``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Creates a copy of the input image. If no data are present (``safe_data is None``),
      logs a warning and returns the original image unchanged.
    - Reshapes the 2D array into blocks of size ``(binning, binning)`` and computes the mean
      over both block dimensions:
      ``image.reshape(H//b, b, W//b, b).mean(-1).mean(1)``.
    - Updates FITS header keywords:
      - ``NAXIS1``, ``NAXIS2`` are set to the new image dimensions.
      - ``CRPIX1``, ``CRPIX2`` are divided by ``binning`` (reference pixel scales with binning).
      - ``DET-BIN1``, ``DET-BIN2``, ``XBINNING``, ``YBINNING``, ``CDELT1``, ``CDELT2`` are multiplied by ``binning``
        (detector binning and pixel scale increase).
    - Header values not listed above (e.g., ``CRVAL*``, ``CTYPE*``) are left unchanged.

    Requirements and limitations
    ----------------------------
    - The input must be a 2D array (``H, W``). Multi-channel arrays are not handled; bin channels
      separately if needed.
    - Both dimensions must be divisible by ``binning``. Otherwise, the internal ``reshape`` will
      raise a :class:`ValueError`.
    - The output dtype will typically be floating-point because block averages are computed
      (e.g., ``float64``); if an integer dtype is required, cast explicitly after processing.

    Flux and photometry considerations
    ----------------------------------
    - This processor uses the arithmetic mean per block. If pixel values represent counts
      (e.g., electrons per pixel) and you wish to conserve total flux, consider summing blocks
      instead of averaging. Averaging changes the per-pixel scaling and reduces summed flux.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` (2D data).
    - Output: :class:`pyobs.images.Image` (copied) with binned data and updated headers.

    Configuration (YAML)
    --------------------
    Bin by a factor of 2:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.SoftBin
       binning: 2

    Bin by a factor of 4:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.SoftBin
       binning: 4

    Notes
    -----
    - This processor is asynchronous; call it within an event loop (using ``await``).
    - If any of the updated header keys are absent, they are skipped; only present keys
      are modified.
    - The processor logs a warning and returns the original image if no data are available.
    """

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, binning: int = 2, **kwargs: Any):
        """Init a new software binning pipeline step.

        Args:
            binning: Binning to apply to image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self.binning = binning

    async def __call__(self, image: Image) -> Image:
        """Bin an image.

        Args:
            image: Image to bin.

        Returns:
            Binned image.
        """

        output_image = image.copy()
        if output_image.safe_data is None:
            log.warning("No data found in image.")
            return image

        output_image.data = self._reshape_image(output_image.data)
        if output_image.safe_data is None:
            log.warning("No data found in image after reshaping.")
            return image

        self._update_header(output_image)

        return output_image

    def _reshape_image(self, image_data: npt.NDArray[np.floating[Any]]) -> npt.NDArray[np.floating[Any]]:
        shape = (image_data.shape[0] // self.binning, self.binning, image_data.shape[1] // self.binning, self.binning)

        return cast(npt.NDArray[np.floating[Any]], image_data.reshape(shape).mean(-1).mean(1))

    def _update_header(self, image: Image) -> None:
        self._update_number_of_pixel_header(image)
        self._update_reference_pixel_header(image)
        self._update_image_scaling_header(image)

    @staticmethod
    def _update_number_of_pixel_header(image: Image) -> None:
        image.header["NAXIS2"], image.header["NAXIS1"] = image.data.shape

    def _update_reference_pixel_header(self, image: Image) -> None:
        for key in ["CRPIX1", "CRPIX2"]:
            if key in image.header:
                image.header[key] /= self.binning

    def _update_image_scaling_header(self, image: Image) -> None:
        for key in ["DET-BIN1", "DET-BIN2", "XBINNING", "YBINNING", "CDELT1", "CDELT2"]:
            if key in image.header:
                image.header[key] *= self.binning


__all__ = ["SoftBin"]
