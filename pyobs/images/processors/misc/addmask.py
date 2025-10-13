from typing import Dict, Any, cast
import logging
import numpy as np
import numpy.typing as npt
from astropy.io import fits

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class AddMask(ImageProcessor):
    """
    Attach a precomputed mask to an image based on instrument and binning.

    This asynchronous processor selects a mask from a user-provided dictionary keyed
    by instrument name and binning, and assigns it to ``image.mask`` in a returned copy
    of the image. Masks can be provided directly as NumPy arrays or as paths to FITS
    files, which are loaded via :func:`astropy.io.fits.getdata`.

    :param dict[str, dict[str, numpy.ndarray | str]] masks: Mapping of instrument name
        (matching ``INSTRUME``) to a mapping of binning strings (e.g., ``"1x1"``,
        ``"2x2"``) to either:
        - a NumPy array mask, or
        - a string path to a FITS file containing the mask array.
        The selected mask must match the image shape for the given instrument and binning.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Builds an internal lookup of masks during initialization:
      - If a value is a NumPy array, it is stored as-is.
      - If a value is a string, loads the mask array using ``fits.getdata(path)``.
      - Otherwise, raises ``ValueError("Unknown mask format.")``.
    - On processing:
      - Reads ``INSTRUME``, ``XBINNING``, and ``YBINNING`` from the FITS header.
      - Constructs the binning key as ``"%dx%d" % (XBINNING, YBINNING)``.
      - Retrieves a copy of the corresponding mask and assigns it to ``output_image.mask``.
      - If no mask is found for the instrument/binning, logs a warning and returns the
        image unchanged.
    - Returns a copy of the input image; pixel data are not modified.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with FITS header keys ``INSTRUME``,
      ``XBINNING``, and ``YBINNING``.
    - Output: :class:`pyobs.images.Image` (copied) with ``mask`` set when available;
      pixel data and other headers are unchanged.

    Configuration (YAML)
    --------------------
    Provide masks for multiple instruments and binning modes, mixing arrays and files:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.AddMask
       masks:
         CAM_A:
           "1x1": "/path/to/cam_a_1x1_mask.fits"
           "2x2": "/path/to/cam_a_2x2_mask.fits"
         CAM_B:
           "1x1": "/path/to/cam_b_1x1_mask.fits"

    Notes
    -----
    - Ensure mask arrays have the same shape as the image data for the selected
      instrument and binning. If your images are color/multi-plane, provide masks
      matching the plane used downstream, or adapt prior processing accordingly.
    - Mask dtype can be boolean or numeric; downstream code typically treats non-zero
      values as masked. Use boolean masks for clarity.
    - The binning key must match the exact ``"%dx%d"`` format built from ``XBINNING``
      and ``YBINNING`` in the image header.
    - Loaded FITS masks use the primary data returned by ``fits.getdata``; if your
      mask resides in a different HDU, adjust accordingly.
    """

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, masks: dict[str, dict[str, npt.NDArray[np.floating[Any]] | str]], **kwargs: Any):
        """Init an image processor that adds a mask to an image.

        Args:
            masks: Dictionary containing instrument->binning->mask, with binning as string, e.g. '1x1'.
        """
        ImageProcessor.__init__(self, **kwargs)

        # masks
        self._masks: dict[str, dict[str, npt.NDArray[np.floating[Any]]]] = {}
        self._build_instrument_dictionary(masks)

    def _build_instrument_dictionary(self, masks: dict[str, dict[str, npt.NDArray[np.floating[Any]] | str]]) -> None:
        for instrument, binning in masks.items():
            self._masks[instrument] = {}
            self._build_binning_dictionary(instrument, binning)

    def _build_binning_dictionary(self, instrument: str, masks: Dict[str, npt.NDArray[np.floating[Any]] | str]) -> None:
        for binning, mask in masks.items():
            if isinstance(mask, np.ndarray):
                self._masks[instrument][binning] = mask
            elif isinstance(mask, str):
                self._masks[instrument][binning] = fits.getdata(mask)
            else:
                raise ValueError("Unknown mask format.")

    def _get_mask(self, image: Image) -> npt.NDArray[np.floating[Any]]:
        instrument = image.header["INSTRUME"]
        binning = "%dx%d" % (image.header["XBINNING"], image.header["YBINNING"])

        return cast(npt.NDArray[np.floating[Any]], self._masks[instrument][binning].copy())

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
