from copy import copy
from typing import Tuple, Any

import numpy as np
from astropy.table import Table

from pyobs.images import ImageProcessor, Image


class ImageSourceFilter(ImageProcessor):
    def __init__(self,
                 min_dist_to_border: float,
                 num_stars: int,
                 min_pixels: int,
                 max_ellipticity: float = 0.4,
                 min_weber_contrast: float = 1.5,
                 max_saturation: int = 50000) -> None:
        """
        Filters the source table after pysep detection has run
        Args:
            min_dist_to_border: Minimal distance to the image border
            num_stars: Number of sources to take
            min_pixels: Minimum required amount of pixels of a source
            max_ellipticity:  Maximum allowed ellipticity of a source
            min_weber_contrast: Minimum required weber contrast of a source (relative to the background)
            max_saturation:
        """

        super().__init__()

        self._min_dist_to_border = min_dist_to_border
        self._num_stars = num_stars
        self._min_pixels = min_pixels
        self._max_ellipticity = max_ellipticity
        self._min_weber_contrast = min_weber_contrast
        self._max_saturation = max_saturation

    async def __call__(self, image: Image) -> Image:
        working_image = copy(image)
        sources_copy = working_image.catalog.copy()

        valid_sources = self.remove_sources_close_to_border(sources_copy, working_image.data.shape)
        good_sources = self.remove_bad_sources(valid_sources)
        selected_sources = self._select_brightest_sources(good_sources)

        working_image.catalog = selected_sources

        return working_image

    @staticmethod
    def _fits2numpy(sources: Table) -> Table:
        """Convert from FITS to numpy conventions for pixel coordinates."""
        for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
            if k in sources.keys():
                sources[k] -= 1
        return sources

    def remove_sources_close_to_border(self, sources: Table, image_shape: Tuple[int, int]) -> Table:
        """Remove table rows from sources when source is closer than given distance from border of image.

        Args:
            sources: Input table.
            image_shape: Shape of image.

        Returns:
            Filtered table.
        ."""

        width, height = image_shape

        x_dist_from_border = width / 2 - np.abs(sources["y"] - width / 2)
        y_dist_from_border = height / 2 - np.abs(sources["x"] - height / 2)

        min_dist_from_border = np.minimum(x_dist_from_border, y_dist_from_border)
        sources_result = sources[min_dist_from_border > self._min_dist_to_border]

        return sources_result

    def remove_bad_sources(
            self, sources: Table,
    ) -> Table:
        """Remove bad sources from table.

        Args:
            sources: Input table.

        Returns:
            Filtered table.
        """

        saturated_sources = sources["peak"] >= self._max_saturation

        small_sources = sources["tnpix"] < self._min_pixels

        tnpix_median = np.median(sources["tnpix"])
        tnpix_std = np.std(sources["tnpix"])
        large_sources = sources["tnpix"] > tnpix_median + 2 * tnpix_std

        elliptic_sources = sources["ellipticity"] > self._max_ellipticity

        background_sources = sources["background"] <= 0

        low_contrast_sources = self._calc_weber_contrast(sources["peak"], sources["background"]) <= self._min_weber_contrast

        bad_sources = saturated_sources | small_sources | large_sources | elliptic_sources | background_sources | low_contrast_sources

        filtered_sources = sources[~bad_sources]  # keep sources that are not bad
        return filtered_sources

    @staticmethod
    def _calc_weber_contrast(peak: np.ndarray[Any, Any], background: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        return (peak - background)/background

    def _select_brightest_sources(self, sources: Table) -> Table:
        """Select the N brightest sources from table.

        Args:
            sources: Source table.

        Returns:
            table containing the N brightest sources.
        """

        sources.sort("flux", reverse=True)

        if 0 < self._num_stars < len(sources):
            sources = sources[:self._num_stars]
        return sources
