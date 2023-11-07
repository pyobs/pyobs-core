import asyncio
import logging
from typing import Tuple, Any

import numpy as np
from astropy.table import Table
from astropy.stats import SigmaClip, sigma_clipped_stats

from pyobs.images import Image
from .sourcedetection import SourceDetection

log = logging.getLogger(__name__)


class DaophotSourceDetection(SourceDetection):
    """Detect source using Daophot."""

    __module__ = "pyobs.images.processors.detection"

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
        self.bkg_sigma = bkg_sigma
        self.bkg_box_size = bkg_box_size
        self.bkg_filter_size = bkg_filter_size

    @staticmethod
    def _gen_catalog_from_source(sources):
        sources.rename_column("xcentroid", "x")
        sources.rename_column("ycentroid", "y")

        # match fits conventions
        sources["x"] += 1
        sources["y"] += 1

        cat = sources["x", "y", "flux", "peak"]

        return cat

    def _estimate_background(self, data: np.ndarray, mask: np.ndarray) -> np.ndarray:
        from photutils import Background2D, MedianBackground

        sigma_clip = SigmaClip(sigma=self.bkg_sigma)
        bkg_estimator = MedianBackground()
        bkg = Background2D(
            data,
            self.bkg_box_size,
            filter_size=self.bkg_filter_size,
            sigma_clip=sigma_clip,
            bkg_estimator=bkg_estimator,
            mask=mask,
        )

        return bkg.background

    def _remove_background_from_data(self, data, mask) -> np.ndarray:
        background = self._estimate_background(data, mask)
        return data - background

    async def _find_stars(self, data: np.ndarray, std: int) -> Table:
        from photutils import DAOStarFinder

        daofind = DAOStarFinder(fwhm=self.fwhm, threshold=self.threshold * std)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, daofind, data)

    @staticmethod
    def _save_catalog_in_image(image: Image, catalog: Table) -> Image:
        output_image = image.copy()
        output_image.catalog = catalog
        return output_image

    async def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """

        if image.data is None:
            log.warning("No data found in image.")
            return image
        image_data = image.data.astype(float)

        background_corrected_data = self._remove_background_from_data(image_data, image.mask)

        _, median, std = sigma_clipped_stats(background_corrected_data, sigma=3.0)

        median_corrected_data = background_corrected_data - median
        sources = await self._find_stars(median_corrected_data, std)

        sources_catalog = self._gen_catalog_from_source(sources)

        return self._save_catalog_in_image(image, sources_catalog)


__all__ = ["DaophotSourceDetection"]
