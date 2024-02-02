from typing import Tuple, List

import numpy as np
import photutils
from astropy.nddata import NDData
from astropy.table import Table
from photutils.psf import EPSFStar

from pyobs.images import Image


class _BoxGenerator(object):
    def __init__(self, num_stars: int, min_pixels: int, min_sources: int) -> None:
        self._num_stars = num_stars
        self._min_pixels = min_pixels
        self._min_sources = min_sources

    def __call__(self, sources: Table, image: Image, star_box_size: float) -> List[EPSFStar]:
        sources = self.remove_sources_close_to_border(sources, image.data.shape, star_box_size // 2 + 1)
        sources = self.remove_bad_sources(sources)
        self._check_sources_count(sources)
        selected_sources = self._select_brightest_sources(sources)

        # extract boxes
        return photutils.psf.extract_stars(
            NDData(image.data.astype(float)), selected_sources, size=star_box_size
        ).all_stars

    @staticmethod
    def _fits2numpy(sources: Table) -> Table:
        """Convert from FITS to numpy conventions for pixel coordinates."""
        for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
            if k in sources.keys():
                sources[k] -= 1
        return sources

    @staticmethod
    def remove_sources_close_to_border(sources: Table, image_shape: Tuple[int, int], min_dist: float) -> Table:
        """Remove table rows from sources when source is closer than given distance from border of image.

        Args:
            sources: Input table.
            image_shape: Shape of image.
            min_dist: Minimum distance from border in pixels.

        Returns:
            Filtered table.
        ."""

        width, height = image_shape

        x_dist_from_border = width / 2 - np.abs(sources["y"] - width / 2)
        y_dist_from_border = height / 2 - np.abs(sources["x"] - height / 2)

        min_dist_from_border = np.minimum(x_dist_from_border, y_dist_from_border)
        sources_result = sources[min_dist_from_border > min_dist]

        return sources_result

    def remove_bad_sources(
            self, sources: Table, max_ellipticity: float = 0.4, min_bkg_factor: float = 1.5, saturation: int = 50000
    ) -> Table:
        """Remove bad sources from table.

        Args:
            sources: Input table.
            max_ellipticity: Maximum ellipticity.
            min_bkg_factor: Minimum factor above local background.
            saturation: Saturation level.

        Returns:
            Filtered table.
        """

        # remove saturated sources
        sources = sources[sources["peak"] < saturation]

        # remove small sources
        sources = sources[sources["tnpix"] >= self._min_pixels]

        # remove large sources
        tnpix_median = np.median(sources["tnpix"])
        tnpix_std = np.std(sources["tnpix"])
        sources = sources[sources["tnpix"] <= tnpix_median + 2 * tnpix_std]

        # remove highly elliptic sources
        sources.sort("ellipticity")
        sources = sources[sources["ellipticity"] <= max_ellipticity]

        # remove sources with background <= 0
        sources = sources[sources["background"] > 0]

        # remove sources with low contrast to background
        sources = sources[(sources["peak"] + sources["background"]) / sources["background"] > min_bkg_factor]
        return sources

    def _select_brightest_sources(self, sources: Table) -> Table:
        """Select the N brightest sources from table.

        Args:
            sources: Source table.

        Returns:
            table containing the N brightest sources.
        """

        sources.sort("flux", reverse=True)

        # extract
        if 0 < self._num_stars < len(sources):
            sources = sources[:self._num_stars]
        return sources

    def _check_sources_count(self, sources: Table) -> None:
        """Check if enough sources in table.

        Args:
            sources: table of sources.

        Returns:
            None

        Raises:
            ValueError if not at least self.min_sources in sources table

        """

        if len(sources) < self._min_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {self._min_sources} required.")
