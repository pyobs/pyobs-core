import logging
from copy import copy
from typing import Any

import numpy as np
from astropy.table import Table, Row

from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    """Estimate exposure time from a star."""

    __module__ = "pyobs.images.processors.exptime"

    SATURATION = 50000

    def __init__(
        self,
        edge: float = 0.1,
        bias: float = 0.0,
        saturated: float = 0.7,
        **kwargs: Any,
    ):
        """Create new exp time estimator from single star.

        Args:
            source_detection: Source detection to use.
            edge: Fraction of image to ignore at each border.
            bias: Bias level of image.
            saturated: Fraction of saturation that is used as brightness limit.
        """
        ExpTimeEstimator.__init__(self, **kwargs)

        self._edge = edge
        self._bias = bias
        self._saturated = saturated

    async def _calc_exp_time(self, image: Image) -> float:
        """
        Process an image and calculates the new exposure time

        Args:
            image: Image to process.
        """

        catalog = image.catalog
        last_exp_time = image.header["EXPTIME"]

        if catalog is None:
            log.info("No catalog found in image.")
            return last_exp_time

        max_peak = self._calc_max_peak(image)

        filtered_catalog = self._filter_saturated_stars(catalog, max_peak)
        brightest_star = self._find_brightest_star(filtered_catalog)

        new_exp_time = self._calc_new_exp_time(last_exp_time, brightest_star["peak"], max_peak)

        return new_exp_time

    def _calc_max_peak(self, image: Image) -> float:
        saturation = self._calc_saturation_level_or_default(image)
        return saturation * self._saturated

    def _calc_saturation_level_or_default(self, image: Image) -> float:
        if "DET-SATU" in image.header and "DET-GAIN" in image.header:
            return image.header["DET-SATU"] / image.header["DET-GAIN"]

        return self.SATURATION

    @staticmethod
    def _filter_saturated_stars(catalog: Table, max_peak: float) -> Table:
        return catalog[catalog["peak"] <= max_peak]

    @staticmethod
    def _find_brightest_star(catalog: Table) -> Row:
        brightest_star_index = np.argmax(catalog["peak"])
        brightest_star = catalog[brightest_star_index]
        return brightest_star

    @staticmethod
    def _log_brightest_star(star: Row):
        log.info("Found peak of %.2f at %.1fx%.1f.", star["peak"], star["x"], star["y"])

    def _calc_new_exp_time(self, exp_time, peak, max_peak):
        return (max_peak - self._bias) / (peak - self._bias) * exp_time


__all__ = ["StarExpTimeEstimator"]
