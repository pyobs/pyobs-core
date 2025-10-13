from copy import copy
from typing import Any, cast
import numpy as np
import numpy.typing as npt
from astropy.table import Table

from pyobs.images import ImageProcessor, Image


class ImageSourceFilter(ImageProcessor):
    """
    Filter a source catalog by border distance, quality metrics, and brightness, selecting the top N stars.

    This asynchronous processor operates on the source catalog attached to a
    :class:`pyobs.images.Image` after SEP-based detection. It removes sources too close
    to the image borders, rejects saturated or low-quality detections based on several
    criteria, and then keeps the brightest remaining sources by flux. Pixel data are
    not modified; the catalog is replaced in a returned copy of the image.

    :param float min_dist_to_border: Minimum allowed distance from any image border,
                                    in pixels. Sources closer than this threshold on
                                    either axis are removed. Default: required.
    :param int num_stars: Number of brightest sources to keep. If set to a positive
                          value smaller than the number of valid sources, the catalog
                          is truncated to that many entries; otherwise all valid sources
                          are kept. Default: required.
    :param int min_pixels: Minimum number of pixels (``tnpix``) required for a source
                           to be considered valid. Default: required.
    :param float max_ellipticity: Maximum allowed source ellipticity. Sources with
                                  ``ellipticity > max_ellipticity`` are removed.
                                  Default: ``0.4``.
    :param float min_weber_contrast: Minimum required Weber contrast relative to the
                                     local background, computed as
                                     ``(peak - background) / background``. Sources with
                                     contrast less than or equal to this value are removed.
                                     Default: ``1.5``.
    :param int max_saturation: Saturation threshold in ADU. Sources with
                               ``peak >= max_saturation`` are considered saturated and
                               removed. Default: ``50000``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Works on a copy of the input image and its catalog.
    - Removes sources near the borders:
      - Computes distance to the nearest border along both axes from the catalog
        coordinates ``x`` and ``y`` and the image shape.
      - Keeps sources whose minimum border distance exceeds ``min_dist_to_border``.
    - Removes low-quality sources using these criteria:
      - Saturation: ``peak >= max_saturation``.
      - Too small: ``tnpix < min_pixels``.
      - Too large: ``tnpix > median(tnpix) + 2 * std(tnpix)`` (to reject extended artifacts).
      - High ellipticity: ``ellipticity > max_ellipticity``.
      - Non-positive background: ``background <= 0``.
      - Low contrast: Weber contrast
        ``(peak - background) / background <= min_weber_contrast``.
    - Selects the brightest sources by sorting on ``flux`` in descending order and
      truncating to ``num_stars`` if positive and less than the number of remaining sources.
    - Returns the modified copy with the filtered catalog assigned.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with a source catalog containing at least
      ``x``, ``y``, ``flux``, ``peak``, ``tnpix``, ``ellipticity``, and ``background``.
      The catalog is expected to use pixel coordinates consistent with the image shape.
    - Output: :class:`pyobs.images.Image` (copied) with a filtered catalog. Pixel data
      and headers are unchanged.

    Configuration (YAML)
    --------------------
    Keep 20 high-quality stars, at least 10 pixels each, away from 25-pixel borders:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.ImageSourceFilter
       min_dist_to_border: 25
       num_stars: 20
       min_pixels: 10
       max_ellipticity: 0.4
       min_weber_contrast: 1.5
       max_saturation: 50000

    Notes
    -----
    - Coordinate convention: pyobs catalogs often store ``x``/``y`` in FITS-like
      1-based pixel coordinates. If necessary, convert to NumPy 0-based indexing
      before applying geometric filters; a helper method ``_fits2numpy`` is provided
      to subtract 1 from common pixel keys but is not invoked automatically here.
    - The border-distance calculation uses the image shape and source positions on
      each axis; ensure consistency between catalog coordinates and image dimensions.
    - The "too large" criterion uses a robust size cutoff based on ``tnpix`` median
      and standard deviation to reject extended artifacts or blends.
    - Weber contrast requires a positive background; sources with non-positive
      background are removed prior to contrast evaluation.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

    def __init__(
        self,
        min_dist_to_border: float,
        num_stars: int,
        min_pixels: int,
        max_ellipticity: float = 0.4,
        min_weber_contrast: float = 1.5,
        max_saturation: int = 50000,
    ) -> None:
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

    def remove_sources_close_to_border(self, sources: Table, image_shape: tuple[int, ...]) -> Table:
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
        self,
        sources: Table,
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

        low_contrast_sources = (
            self._calc_weber_contrast(sources["peak"], sources["background"]) <= self._min_weber_contrast
        )

        bad_sources = (
            saturated_sources
            | small_sources
            | large_sources
            | elliptic_sources
            | background_sources
            | low_contrast_sources
        )

        filtered_sources = sources[~bad_sources]  # keep sources that are not bad
        return filtered_sources

    @staticmethod
    def _calc_weber_contrast(
        peak: npt.NDArray[np.floating[Any]],
        background: npt.NDArray[np.floating[Any]],
    ) -> npt.NDArray[np.floating[Any]]:
        return cast(npt.NDArray[np.floating[Any]], (peak - background) / background)

    def _select_brightest_sources(self, sources: Table) -> Table:
        """Select the N brightest sources from table.

        Args:
            sources: Source table.

        Returns:
            table containing the N brightest sources.
        """

        sources.sort("flux", reverse=True)

        if 0 < self._num_stars < len(sources):
            sources = sources[: self._num_stars]
        return sources


__all__ = ["ImageSourceFilter"]
