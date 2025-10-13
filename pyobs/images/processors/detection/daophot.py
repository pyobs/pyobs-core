import asyncio
import logging
from typing import Tuple, Any
import numpy as np
import numpy.typing as npt
from astropy.stats import sigma_clipped_stats
from astropy.table import Table

from pyobs.images import Image
from ._source_catalog import _SourceCatalog
from .sourcedetection import SourceDetection
from .._daobackgroundremover import _DaoBackgroundRemover

log = logging.getLogger(__name__)


class DaophotSourceDetection(SourceDetection):
    """
    Detect astronomical point sources using a DAOPhot-style algorithm via photutils.

    This asynchronous processor estimates and removes the background of a
    :class:`pyobs.images.Image`, computes robust image statistics, and then detects
    point-like sources using :class:`photutils.detection.DAOStarFinder`. The resulting
    source table is converted into a pyobs catalog and attached to the image. Pixel
    data are not modified in the returned image.

    :param float fwhm: Estimated point-spread-function full width at half maximum (FWHM)
                       in pixels. Used by DAOStarFinder to construct its matched filter.
                       Default: ``3.0``.
    :param float threshold: Detection threshold in units of the background standard
                            deviation (sigma). The effective pixel threshold passed to
                            DAOStarFinder is ``threshold * std`` where ``std`` is measured
                            from the background-subtracted image. Default: ``4.0``.
    :param float bkg_sigma: Sigma for kappa–sigma clipping in background estimation and
                            statistics. Passed to the internal background remover.
                            Default: ``3.0``.
    :param tuple[int, int] bkg_box_size: Box size (ny, nx) in pixels for the background
                                         estimation grid used by the background remover.
                                         Default: ``(50, 50)``.
    :param tuple[int, int] bkg_filter_size: Smoothing filter size (ny, nx) in pixels
                                            applied to the coarse background map.
                                            Default: ``(3, 3)``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.detection.SourceDetection`.

    Behavior
    --------
    - If the input image has no data (``image.safe_data is None``), a warning is logged
      and the image is returned unchanged.
    - Background is estimated and subtracted using
      :class:`pyobs.images.processors.detection._DaoBackgroundRemover`
      with the configured ``bkg_sigma``, ``bkg_box_size``, and ``bkg_filter_size``.
    - Robust statistics are computed on the background-corrected data via
      :func:`astropy.stats.sigma_clipped_stats` (with ``sigma=3.0``) to obtain
      median and standard deviation.
    - The median is subtracted from the background-corrected data, and
      :class:`photutils.detection.DAOStarFinder` is run with
      ``fwhm=self.fwhm`` and ``threshold=self.threshold * std``.
    - DAOStarFinder execution is offloaded to a thread executor to avoid blocking
      the event loop.
    - The resulting :class:`astropy.table.Table` is converted to a pyobs
      :class:`pyobs.images.catalog._SourceCatalog`, FITS 1-based origin convention is
      applied to coordinates, and the catalog is attached to the image with the keys
      ``["x", "y", "flux", "peak"]``.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with 2D pixel data.
    - Output: :class:`pyobs.images.Image` with a source catalog attached. Pixel data
      are unchanged; catalog entries typically include positions and flux measures.

    Configuration (YAML)
    --------------------
    Minimal example:

    .. code-block:: yaml

       class: pyobs.images.processors.detection.DaophotSourceDetection
       fwhm: 3.0
       threshold: 4.0

    Tune background estimation and sensitivity:

    .. code-block:: yaml

       class: pyobs.images.processors.detection.DaophotSourceDetection
       fwhm: 2.5
       threshold: 5.0
       bkg_box_size: [64, 64]
       bkg_filter_size: [3, 3]

    Notes
    -----
    - ``fwhm`` must be given in pixels. An accurate FWHM improves detection quality,
      especially in crowded fields or variable seeing.
    - ``threshold`` is a global sigma threshold referenced to the measured background
      noise; very low values may increase false positives.
    - The background remover’s exact behavior (e.g., clipping strategy, box tiling,
      and filtering) is defined by
      :class:`pyobs.images.processors.detection._DaoBackgroundRemover`.
    - Very bright/saturated sources or artifacts (cosmic rays, bleed trails) may
      produce spurious detections; consider pre-masking if necessary.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

    __module__ = "pyobs.images.processors.detection"

    _CATALOG_KEYS = ["x", "y", "flux", "peak"]

    def __init__(
        self,
        fwhm: float = 3.0,
        threshold: float = 4.0,
        bkg_sigma: float = 3.0,
        bkg_box_size: Tuple[int, int] = (50, 50),
        bkg_filter_size: Tuple[int, int] = (3, 3),
        **kwargs: Any,
    ):
        """Initializes a wrapper for photutils. See its documentation for details.

        Args:
            fwhm: Full-width at half maximum for Gaussian kernel.
            threshold: Threshold pixel value for detection in standard deviations.
            bkg_sigma: Sigma for background kappa-sigma clipping.
            bkg_box_size: Box size for background estimation.
            bkg_filter_size: Filter size for background estimation.
        """
        SourceDetection.__init__(self, **kwargs)

        # store
        self.fwhm = fwhm
        self.threshold = threshold

        self._background_remover = _DaoBackgroundRemover(bkg_sigma, bkg_box_size, bkg_filter_size)

    async def _find_stars(self, data: npt.NDArray[np.floating[Any]], std: int) -> Table:
        from photutils.detection import DAOStarFinder

        daofind = DAOStarFinder(fwhm=self.fwhm, threshold=self.threshold * std)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, daofind, data)

    async def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """

        if image.safe_data is None:
            log.warning("No data found in image.")
            return image

        background_corrected_image = self._background_remover(image)
        background_corrected_data = background_corrected_image.data.astype(float)

        _, median, std = sigma_clipped_stats(background_corrected_data, sigma=3.0)

        median_corrected_data = background_corrected_data - median
        sources = await self._find_stars(median_corrected_data, std)

        sources_catalog = _SourceCatalog.from_table(sources)
        sources_catalog.apply_fits_origin_convention()
        output_image = sources_catalog.save_to_image(image, self._CATALOG_KEYS)
        return output_image


__all__ = ["DaophotSourceDetection"]
