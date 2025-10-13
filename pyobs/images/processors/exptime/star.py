import logging
from copy import copy
from typing import Any, Optional

import numpy as np
from astropy.table import Row

from pyobs.images import Image
from pyobs.images.processors.exptime.exptime import ExpTimeEstimator

log = logging.getLogger(__name__)


class StarExpTimeEstimator(ExpTimeEstimator):
    """
    Estimate a new exposure time from the brightest unsaturated star in the image.

    This asynchronous processor inspects a source catalog attached to a
    :class:`pyobs.images.Image`, filters out saturated and edge-affected stars, selects
    the brightest remaining star, and scales the current exposure time so that the
    star would reach a configurable fraction of the detector saturation. The scaling
    uses a bias-corrected linear relation. The recommended exposure time is returned
    as a float; pixel data are not modified.

    :param float edge: Fraction of the image to ignore at each border (on both sides
                       of x and y). A value of 0.1 excludes the outer 10% of the image
                       width and height. Default: ``0.0``.
    :param float bias: Bias level in ADU to subtract from measured peaks in the
                       exposure-time scaling formula. Default: ``0.0``.
    :param float saturated: Target fraction of the detector saturation to aim for
                            with the brightest star (e.g., ``0.7`` for 70% of saturation).
                            Default: ``0.7``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.exptime.ExpTimeEstimator`.

    Behavior
    --------
    - Reads the current exposure time from ``image.header["EXPTIME"]``.
    - If the image has no source catalog (``image.safe_catalog is None``), returns the
      current exposure time unchanged.
    - Determines the detector saturation level in ADU:
      - If both ``DET-SATU`` (saturation in electrons) and ``DET-GAIN`` (e⁻/ADU) are
        present in the header, uses ``DET-SATU / DET-GAIN``.
      - Otherwise, uses a default saturation of ``50000`` ADU.
    - Removes saturated stars from the catalog by keeping entries with
      ``peak <= saturation``.
    - Excludes stars near the image borders on both axes:
      - The axis lengths are read from ``NAXIS0`` (x) and ``NAXIS1`` (y) in the header.
      - Stars must satisfy ``x >= 1 + edge_size`` and ``x <= axis_len - edge_size``
        (analogously for ``y``), where ``edge_size = edge * axis_len``.
      - Coordinates are expected to use FITS 1-based convention.
    - Selects the brightest remaining star by the ``peak`` column and computes the
      target peak as ``target = saturated * saturation``.
    - Computes the new exposure time with bias correction:
      ``t_new = (target - bias) / (peak - bias) * t_old``.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with a source catalog containing at least
      ``x``, ``y``, and ``peak`` columns, and a FITS header with ``EXPTIME``. Optional
      ``DET-SATU`` and ``DET-GAIN`` improve saturation estimation.
    - Output: ``float`` recommended exposure time. Pixel data and headers are unchanged.

    Configuration (YAML)
    --------------------
    Aim for 70% of saturation and ignore 5% borders:

    .. code-block:: yaml

       class: pyobs.images.processors.exptime.StarExpTimeEstimator
       edge: 0.05
       saturated: 0.7
       bias: 0.0

    Notes
    -----
    - The formula assumes linear detector response in ADU after bias correction.
      If ``peak <= bias``, the scaling becomes ill-defined; ensure peaks are above
      the bias level.
    - Accurate gain (``DET-GAIN``) and saturation (``DET-SATU``) metadata yield more
      reliable targets; otherwise the default saturation of 50000 ADU is used.
    - Edge filtering helps avoid truncated or aberrant stars near the borders that
      would bias the estimate.
    - If all stars are filtered out, the brightest-star selection may fail; ensure
      reasonable detection and filtering parameters or handle empty catalogs upstream.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

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
