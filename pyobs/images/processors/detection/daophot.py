import asyncio
import logging
from typing import Tuple, Any

import numpy as np
from astropy.stats import sigma_clipped_stats
from astropy.table import Table

from pyobs.images import Image
from ._source_catalog import _SourceCatalog
from .sourcedetection import SourceDetection
from .._daobackgroundremover import _DaoBackgroundRemover

log = logging.getLogger(__name__)


class DaophotSourceDetection(SourceDetection):
    """Detect source using Daophot."""

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

    async def _find_stars(self, data: np.ndarray, std: int) -> Table:
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
