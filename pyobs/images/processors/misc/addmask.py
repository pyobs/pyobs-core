from typing import Dict, Any
import logging
import numpy as np
from astropy.io import fits

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class AddMask(ImageProcessor):
    """Add mask to image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self, masks: dict[str, dict[str, np.ndarray[tuple[int, int], np.dtype[np.number]] | str]], **kwargs: Any
    ):
        """Init an image processor that adds a mask to an image.

        Args:
            masks: Dictionary containing instrument->binning->mask, with binning as string, e.g. '1x1'.
        """
        ImageProcessor.__init__(self, **kwargs)

        # masks
        self._masks: dict[str, dict[str, np.ndarray[tuple[int, int], np.dtype[np.number]]]] = {}
        self._build_instrument_dictionary(masks)

    def _build_instrument_dictionary(
        self, masks: dict[str, dict[str, np.ndarray[tuple[int, int], np.dtype[np.number]] | str]]
    ) -> None:
        for instrument, binning in masks.items():
            self._masks[instrument] = {}
            self._build_binning_dictionary(instrument, binning)

    def _build_binning_dictionary(
        self, instrument: str, masks: Dict[str, np.ndarray[tuple[int, int], np.dtype[np.number]] | str]
    ) -> None:
        for binning, mask in masks.items():
            if isinstance(mask, np.ndarray):
                self._masks[instrument][binning] = mask
            elif isinstance(mask, str):
                self._masks[instrument][binning] = fits.getdata(mask)
            else:
                raise ValueError("Unknown mask format.")

    def _get_mask(self, image: Image) -> np.ndarray[tuple[int, int], np.dtype[np.number]]:
        instrument = image.header["INSTRUME"]
        binning = "%dx%d" % (image.header["XBINNING"], image.header["YBINNING"])

        return self._masks[instrument][binning].copy()

    async def __call__(self, image: Image) -> Image:
        """Add mask to image.

        Args:
            image: Image to add mask to.

        Returns:
            Image with mask
        """

        output_image = image.copy()

        try:
            output_image.mask = self._get_mask(image)
        except KeyError:
            log.warning("No mask found for binning of frame.")

        return output_image


__all__ = ["AddMask"]
