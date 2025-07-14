import logging
from copy import copy
from typing import Any, Optional

import numpy as np
from astropy.table import Row

from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    """Estimate exposure time from a star."""

    __module__ = "pyobs.images.processors.exptime"

    SATURATION = 50000

    def __init__(
        self,
        edge: float = 0.0,
        bias: float = 0.0,
        saturated: float = 0.7,
        **kwargs: Any,
    ):
        """Create new exp time estimator from single star.

        Args:
            edge: Fraction of image to ignore at each border.
            bias: Bias level of image.
            saturated: Fraction of saturation that is used as brightness limit.
        """
        ExpTimeEstimator.__init__(self, **kwargs)

        self._edge = edge
        self._bias = bias
        self._saturated = saturated

        self._image: Optional[Image] = None

    async def _calc_exp_time(self, image: Image) -> float:
        """
        Process an image and calculates the new exposure time

        Args:
            image: Image to process.
        """

        self._image = copy(image)
        last_exp_time: float = image.header["EXPTIME"]

        if self._image.safe_catalog is None:
            log.info("No catalog found in image.")
            return last_exp_time

        saturation = self._calc_saturation_level_or_default()
        self._filter_saturated_stars(saturation)
        self._filter_edge_stars()
        brightest_star = self._find_brightest_star()

        target_saturation = self._calc_target_saturation(saturation)
        new_exp_time = self._calc_new_exp_time(last_exp_time, brightest_star["peak"], target_saturation)

        return new_exp_time

    def _calc_target_saturation(self, saturation: float) -> float:
        return saturation * self._saturated

    def _calc_saturation_level_or_default(self) -> float:
        if self._image is None:
            raise RuntimeError("No image available.")
        if "DET-SATU" in self._image.header and "DET-GAIN" in self._image.header:
            return float(self._image.header["DET-SATU"] / self._image.header["DET-GAIN"])
        return self.SATURATION

    def _filter_saturated_stars(self, max_peak: float) -> None:
        if self._image is None:
            raise RuntimeError("No image available.")
        self._image.catalog = self._image.catalog[self._image.catalog["peak"] <= max_peak]

    def _filter_edge_stars(self) -> None:
        self._filter_edge_stars_axis(0)
        self._filter_edge_stars_axis(1)

    def _filter_edge_stars_axis(self, axis: int) -> None:
        if self._image is None:
            raise RuntimeError("No image available.")

        axis_len = int(self._image.header[f"NAXIS{axis}"])
        edge_size = int(axis_len * self._edge)

        axis_name = ["x", "y"][axis]

        self._image.catalog = self._image.catalog[self._image.catalog[axis_name] >= 1 + edge_size]
        self._image.catalog = self._image.catalog[self._image.catalog[axis_name] <= axis_len - edge_size]

    def _find_brightest_star(self) -> Row:
        if self._image is None:
            raise RuntimeError("No image available.")

        brightest_star_index = np.argmax(self._image.catalog["peak"])
        brightest_star = self._image.catalog[brightest_star_index]
        return brightest_star

    @staticmethod
    def _log_brightest_star(star: Row) -> None:
        log.info("Found peak of %.2f at %.1fx%.1f.", star["peak"], star["x"], star["y"])

    def _calc_new_exp_time(self, exp_time: float, peak: float, max_peak: float) -> float:
        return (max_peak - self._bias) / (peak - self._bias) * exp_time


__all__ = ["StarExpTimeEstimator"]
