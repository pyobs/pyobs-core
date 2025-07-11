import logging
from typing import Any, cast
import numpy as np

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SoftBin(ImageProcessor):
    """Bin an image."""

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

    def _reshape_image(
        self, image_data: np.ndarray[tuple[int, int], np.dtype[np.number]]
    ) -> np.ndarray[tuple[int, int], np.dtype[np.number]]:
        shape = (image_data.shape[0] // self.binning, self.binning, image_data.shape[1] // self.binning, self.binning)

        return cast(np.ndarray[tuple[int, int], np.dtype[np.number]], image_data.reshape(shape).mean(-1).mean(1))

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
