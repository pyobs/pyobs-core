import logging
from copy import copy
from typing import Any

from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    """Estimate exposure time from a star."""

    __module__ = "pyobs.images.processors.exptime"

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
        self.coordinates = (None, None)

    async def _calc_exp_time(self, image: Image) -> float:
        """
        Process an image and calculates the new exposure time

        Args:
            image: Image to process.
        """

        catalog = copy(image.catalog)

        if catalog is None:
            log.info("No catalog found in image.")
            return image.header["EXPTIME"]

        # sort catalog by peak flux
        catalog.sort("peak", reverse=True)

        # saturation level
        if "DET-SATU" in image.header and "DET-GAIN" in image.header:
            saturation = image.header["DET-SATU"] / image.header["DET-GAIN"]
        else:
            saturation = 50000

        # get max peak flux that we allow
        max_peak = saturation * self._saturated

        # filter out all stars that are saturated
        catalog = catalog[catalog["peak"] <= max_peak]

        # get brightest star, get its peak flux and store its coordinates
        star = catalog[0]
        peak = star["peak"]
        log.info("Found peak of %.2f at %.1fx%.1f.", star["peak"], star["x"], star["y"])
        self.coordinates = (star["x"], star["y"])

        # get exposure time of image
        exp_time = image.header["EXPTIME"]

        # calculate new exposure time and return it
        new_exp_time = exp_time / (peak - self._bias) * (max_peak - self._bias)

        return new_exp_time


__all__ = ["StarExpTimeEstimator"]
