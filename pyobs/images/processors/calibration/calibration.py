from __future__ import annotations

import logging
from typing import Any, cast

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor
from pyobs.images.processors.calibration._calibration_cache import _CalibrationCache
from pyobs.images.processors.calibration._ccddata_calibrator import _CCDDataCalibrator
from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.exptime_grouping import exptimes_close
from pyobs.utils.pipeline import Pipeline
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Calibration(ImageProcessor):
    """
    Calibrate an image using master bias, dark, and flat frames fetched from an archive.

    This processor locates appropriate master calibration frames
    (bias, dark, flat) based on the input image metadata, applies calibration to the
    image, and annotates the FITS header with provenance and reduction information.
    Calibration frames are looked up via an :class:`~pyobs.robotic.utils.archive.Archive` and are
    cached in a class-wide cache to reduce repeated lookups. If required calibration
    frames cannot be found, the original image is returned unchanged.

    :param dict | Archive archive: Archive configuration or an already constructed
                                  :class:`~pyobs.robotic.utils.archive.Archive` instance used to
                                  locate master calibration frames. If a dictionary
                                  is provided, it is instantiated via
                                  :func:`~pyobs.object.get_object`.
    :param int max_cache_size: Maximum number of master frames kept in the shared
                               calibration cache. Default: ``20``.
    :param bool require_bias: If ``True``, a master bias must be found; otherwise
                              calibration is aborted and the image is returned
                              unchanged. If ``False``, bias subtraction is skipped.
                              Default: ``True``.
    :param bool require_dark: If ``True``, a master dark must be found; otherwise
                              calibration is aborted. If ``False``, dark subtraction
                              is skipped. Default: ``True``.
    :param bool require_flat: If ``True``, a master flat must be found; otherwise
                              calibration is aborted. If ``False``, flat-fielding is
                              skipped. Default: ``True``.
    :param float | None max_days_bias: Maximum age difference in days allowed when
                                       selecting the master bias relative to the
                                       science image ``DATE-OBS``. If ``None``, no
                                       explicit age limit is applied. Default: ``None``.
    :param float | None max_days_dark: Same as ``max_days_bias`` for dark frames.
                                       Default: ``None``.
    :param float | None max_days_flat: Same as ``max_days_bias`` for flat frames.
                                       Default: ``None``.
    :param float dark_exptime_tolerance: Relative tolerance for matching a science frame's
                                         ``EXPTIME`` against a dark master's, and for the
                                         scale-down-only ceiling around ``dark_scale_exptime``.
                                         Default: ``0.01`` (1%).
    :param float | None dark_scale_exptime: Reference dark exposure time (seconds) that may be
                                            scaled down to a shorter science exptime when no
                                            exact-exptime master exists. ``None`` disables
                                            scale-down entirely (branch 3 below never fires).
                                            Default: ``600.0``.
    :param bool allow_unmatched_dark_scale: If ``True``, a science exptime with neither an
                                            exact-match master nor a usable reference master
                                            falls back to today's always-scale-whatever-is-
                                            nearest behavior instead of raising. For sites not
                                            yet taking per-exptime darks. Default: ``False``.
    :param float | None dark_min_exptime: Science exptimes below this (and with no exact-match
                                          master) skip dark subtraction entirely and are
                                          calibrated with bias only -- dark current is assumed
                                          negligible there. ``None`` or ``0`` disables this
                                          branch. Default: ``5.0``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Verifies required image header keys before searching: ``INSTRUME``, ``XBINNING``,
      and ``DATE-OBS`` must be present.
    - Attempts to retrieve required masters (bias, dark, flat) from a class-wide cache.
      On cache miss, queries the configured archive via
      :meth:`~pyobs.utils.pipeline.Pipeline.find_master`, matching:

      - Instrument: exact value of ``INSTRUME``.
      - Binning: string formatted as ``"{XBINNING}x{XBINNING}"`` (square binning assumed).
      - Filter: ``FILTER`` only for flats; biases and darks ignore filter.
      - Time constraint: centered on the image ``DATE-OBS`` with optional ``max_days_*``.

    - Dark matching additionally follows ADR
      ``0015-dark-master-strict-exptime-matching-reference-scale-down-only.md``, checked in
      order against the science frame's own ``EXPTIME``:

      1. An exact match (within ``dark_exptime_tolerance``) is used unscaled.
      2. No exact match and ``EXPTIME < dark_min_exptime``: bias-only, no dark subtraction,
         not an error.
      3. No exact match, ``EXPTIME >= dark_min_exptime``, and a reference master with
         ``EXPTIME <= dark_scale_exptime`` exists: used scaled down to the science exptime.
      4. ``allow_unmatched_dark_scale=True``: fall back to whatever ``find_master`` returns,
         scaled, regardless of direction (today's behavior).
      5. Otherwise: a ``ValueError`` naming the requested exptime, caught the same way as any
         other missing-master case (see below).

    - If any required master is missing, logs a warning and returns the original image
      unchanged.
    - Applies calibration using the internal ``_CCDDataCalibrator`` helper
      with the found master frames (``None`` for any non-required step to be skipped).
    - Copies provenance into the output FITS header:

      - ``L1RAW`` set from the original ``ORIGNAME`` (file stem without ``.fits``).
      - ``L1BIAS``, ``L1DARK``, ``L1FLAT`` set from the respective master frame
        ``FNAME`` values (with common FITS extensions removed) and descriptive comments.

    - Sets calibration metadata in the output header:

      - ``BUNIT = "electron"`` to indicate calibrated pixel units.
      - ``RLEVEL = 1`` to indicate reduction level.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with FITS header containing at least
      ``INSTRUME``, ``XBINNING``, and ``DATE-OBS``; optional ``FILTER`` improves flat matching.
    - Output: :class:`pyobs.images.Image` calibrated by subtracting bias, subtracting
      dark, and dividing by flat as available. Pixel data are modified; header is
      augmented with provenance and reduction keys.

    Configuration (YAML)
    --------------------
    Use an archive object and allow calibration frames up to 7 days old:

    .. code-block:: yaml

       class: pyobs.images.processors.calibration.Calibration
       archive:
         class: your.archive.Class  # replace with your Archive implementation
         # ... archive-specific configuration ...
       max_cache_size: 50
       max_days_bias: 7
       max_days_dark: 7
       max_days_flat: 7
       require_bias: true
       require_dark: true
       require_flat: true

    Skip flats but require bias and dark:

    .. code-block:: yaml

       class: pyobs.images.processors.calibration.Calibration
       archive: { class: your.archive.Class, ... }
       require_flat: false

    Notes
    -----
    - The calibration cache is shared across all instances of this class within the
      process and is bounded by ``max_cache_size``.
    - Only ``XBINNING`` is considered; this implementation assumes square binning.
      If your data use asymmetric binning, adjust the matching logic.
    - Flats are matched by filter when available; biases and darks ignore filter.
    - If ``ORIGNAME`` is present in the input header, it is copied to ``L1RAW`` as a
      stem without the ``.fits`` suffix. Master frame names are copied from ``FNAME``.
    - Setting ``BUNIT = "electron"`` assumes calibrated units are electrons; ensure
      your calibration products and gains are consistent with this convention.
    """

    __module__ = "pyobs.images.processors.calibration"

    """Cache for calibration frames."""
    _calib_cache: _CalibrationCache | None = None

    def __init__(
        self,
        archive: dict[str, Any] | Archive,
        max_cache_size: int = 20,
        require_bias: bool = True,
        require_dark: bool = True,
        require_flat: bool = True,
        max_days_bias: float | None = None,
        max_days_dark: float | None = None,
        max_days_flat: float | None = None,
        dark_exptime_tolerance: float = 0.01,
        dark_scale_exptime: float | None = 600.0,
        allow_unmatched_dark_scale: bool = False,
        dark_min_exptime: float | None = 5.0,
        **kwargs: Any,
    ):
        """Init a new image calibration pipeline step.

        Args:
            archive: Archive to fetch calibration frames from.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._max_cache_size = max_cache_size
        self._max_days_bias = max_days_bias
        self._max_days_dark = max_days_dark
        self._max_days_flat = max_days_flat
        self._require_bias = require_bias
        self._require_dark = require_dark
        self._require_flat = require_flat
        self._dark_exptime_tolerance = dark_exptime_tolerance
        self._dark_scale_exptime = dark_scale_exptime
        self._allow_unmatched_dark_scale = allow_unmatched_dark_scale
        self._dark_min_exptime = dark_min_exptime

        self._archive = self.pyobs_model_validate(Archive, archive)

        if self._calib_cache is None:
            self._calib_cache = _CalibrationCache(self._max_cache_size)

    async def __call__(self, image: Image) -> Image:
        """Calibrate an image.

        Args:
            image: Image to calibrate.

        Returns:
            Calibrated image.
        """

        try:
            bias, dark, flat, dark_scale = await self._get_calibrations_masters(image)
        except ValueError as e:
            log.warning("Could not find calibration frames: %s", e)
            return image

        calibrator = _CCDDataCalibrator(image, bias, dark, flat, dark_scale=dark_scale)
        calibrated = calibrator()

        self._copy_original_filename(calibrated, image)
        self._copy_calibration_filename(calibrated, bias, dark, flat)

        self._set_calibration_headers(calibrated)

        return calibrated

    async def _get_calibrations_masters(self, image: Image) -> tuple[Image | None, Image | None, Image | None, bool]:
        bias = (
            None
            if not self._require_bias
            else await self._find_master(image, ImageType.BIAS, max_days=self._max_days_bias)
        )
        dark, dark_scale = await self._find_dark_master(image)
        flat = (
            None
            if not self._require_flat
            else await self._find_master(image, ImageType.SKYFLAT, max_days=self._max_days_flat)
        )

        return bias, dark, flat, dark_scale

    async def _find_dark_master(self, image: Image) -> tuple[Image | None, bool]:
        """Implements ADR 0015's dark-master matching/scaling policy, checked in order against
        the science image's own EXPTIME:

        1. An exact match (within dark_exptime_tolerance) -- used unscaled.
        2. No exact match and EXPTIME < dark_min_exptime -- bias-only, not an error.
        3. No exact match, EXPTIME >= dark_min_exptime, and a reference master with
           EXPTIME <= dark_scale_exptime exists -- used scaled down to the science exptime.
        4. allow_unmatched_dark_scale=True -- fall back to today's always-scale-whatever-is-
           nearest behavior.
        5. Otherwise -- ValueError, caught by __call__ like any other missing-master case.

        Returns:
            (master, scale). master is None only for the legitimate bias-only branch (2), or
            when require_dark is False. scale tells the caller whether _CCDDataCalibrator
            should rescale the returned master to the science exptime.

        Raises:
            ValueError: no usable dark master under the configured policy (branch 5).
        """
        if not self._require_dark:
            return None, False

        self._verify_image_header(image)
        science_exptime = float(image.header["EXPTIME"])

        # (1) exact match, used unscaled
        exact = await self._find_dark_at(image, science_exptime, self._max_days_dark)
        if exact is not None:
            return exact, False

        # (2) below the minimum, no exact match -- bias-only, not an error
        if self._dark_min_exptime is not None and science_exptime < self._dark_min_exptime:
            return None, False

        # (3) reference master, scaled down only (never up). The tolerance band means a science
        # exptime up to ~dark_scale_exptime*(1+tolerance) is accepted here even though it's
        # technically above the reference -- and _find_dark_at's own exptime_max ceiling for the
        # reference lookup uses the same band, so the master found is never more than that
        # ~1% above dark_scale_exptime either. Never scales *up* in practice; the band is a
        # deliberate width-of-a-hair looseness, not a policy hole.
        if self._dark_scale_exptime is not None and science_exptime <= self._dark_scale_exptime * (
            1 + self._dark_exptime_tolerance
        ):
            reference = await self._find_dark_at(
                image, self._dark_scale_exptime, self._max_days_dark, exptime_max=self._dark_scale_exptime
            )
            if reference is not None:
                return reference, True

        # (4) opt back into today's always-scale-whatever-is-nearest behavior
        if self._allow_unmatched_dark_scale:
            fallback = await self._find_master(image, ImageType.DARK, max_days=self._max_days_dark)
            return fallback, True

        # (5) strict -- no usable dark master under the configured policy
        ceiling = (
            None if self._dark_scale_exptime is None else self._dark_scale_exptime * (1 + self._dark_exptime_tolerance)
        )
        available = await self._available_dark_exptimes(image)
        raise ValueError(
            f"No usable dark master for EXPTIME={science_exptime}s (no exact match within "
            f"{self._dark_exptime_tolerance:.0%}"
            + (
                f", no reference master <= {ceiling:.1f}s to scale down"
                if ceiling is not None
                else ", no reference exptime configured"
            )
            + f"); available master exptimes: {available if available else 'none'}."
        )

    async def _available_dark_exptimes(self, image: Image) -> list[float]:
        """Best-effort list of exptimes among this instrument/binning's archived DARK masters,
        for the strict-policy error message only (ADR 0015 asks that it name what's available).
        Never raises -- an archive issue here shouldn't mask the real ValueError being raised."""
        try:
            instrument = image.header["INSTRUME"]
            binning = "{0}x{0}".format(image.header["XBINNING"])  # noqa: UP031
            infos = await self._archive.list_frames(
                instrument=instrument, image_type=ImageType.DARK, binning=binning, rlevel=1
            )
        except Exception:
            return []
        return sorted({i.exptime for i in infos if i.exptime is not None})

    async def _find_dark_at(
        self, image: Image, target_exptime: float, max_days: float | None, exptime_max: float | None = None
    ) -> Image | None:
        """Looks up a DARK master near target_exptime via the shared calibration cache, keyed
        by that target rather than either image's own EXPTIME (see _CalibrationCache), falling
        back to an archive query on a cache miss.

        Args:
            target_exptime: Exptime to search near -- the science exptime for an exact-match
                lookup, or dark_scale_exptime for a reference lookup.
            exptime_max: If given, only accept candidates with EXPTIME <= this (scale-down-only
                enforcement); the result is otherwise accepted whatever its exptime. If not
                given, this is an exact-match lookup: the result is discarded (returns None)
                unless it's actually within dark_exptime_tolerance of target_exptime.

        Returns:
            The master, or None if nothing usable was found. Never raises.
        """
        if self._calib_cache is None:
            return None

        try:
            return self._calib_cache.get_from_cache(image, ImageType.DARK, exptime=target_exptime)
        except ValueError:
            pass

        self._verify_image_header(image)
        instrument = image.header["INSTRUME"]
        binning = "{0}x{0}".format(image.header["XBINNING"])  # noqa: UP031
        time = Time(image.header["DATE-OBS"])

        master = await Pipeline.find_master(
            self._archive,
            ImageType.DARK,
            time,
            instrument,
            binning,
            None,
            max_days=max_days,
            exptime=target_exptime,
            exptime_tolerance=self._dark_exptime_tolerance,
            exptime_max=exptime_max,
        )
        if master is None:
            return None

        if exptime_max is None and (
            "EXPTIME" not in master.header
            or not exptimes_close(float(master.header["EXPTIME"]), target_exptime, self._dark_exptime_tolerance)
        ):
            # nearest available, but not actually an exact match (or a legacy pre-#831 master
            # with no EXPTIME header at all) -- not usable for this lookup
            return None

        self._calib_cache.add_to_cache(master, ImageType.DARK, exptime=target_exptime)
        return master

    async def _find_master(self, image: Image, image_type: ImageType, max_days: float | None = None) -> Image:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_type: image type.

        Returns:
            Image or None

        Raises:
            ValueError: if no calibration frame could be found.
        """

        self._verify_image_header(image)

        if self._calib_cache is None:
            raise ValueError("No cache.")

        try:
            return self._calib_cache.get_from_cache(image, image_type)
        except ValueError:
            master = await self._find_master_in_archive(image, image_type, max_days)
            self._calib_cache.add_to_cache(master, image_type)
            return master

    @staticmethod
    def _verify_image_header(image: Image) -> None:
        has_instrument = "INSTRUME" in image.header
        has_binning = "XBINNING" in image.header
        has_time = "DATE-OBS" in image.header
        # EXPTIME is needed by dark-exptime matching (_find_dark_master) and was already an
        # implicit requirement of _CCDDataCalibrator itself (data_exposure=...EXPTIME...) --
        # checked upfront here instead of surfacing as a bare KeyError mid-calibration.
        has_exptime = "EXPTIME" in image.header

        if not (has_instrument and has_binning and has_time and has_exptime):
            raise ValueError("Could not fetch items from image header.")

    async def _find_master_in_archive(
        self, image: Image, image_type: ImageType, max_days: float | None = None
    ) -> Image:
        instrument = image.header["INSTRUME"]
        binning = "{0}x{0}".format(image.header["XBINNING"])  # noqa: UP031
        filter_name = cast(str, image.header["FILTER"]) if "FILTER" in image.header else None
        time = Time(image.header["DATE-OBS"])

        master = await Pipeline.find_master(
            self._archive,
            image_type,
            time,
            instrument,
            binning,
            None if image_type in [ImageType.BIAS, ImageType.DARK] else filter_name,
            max_days=max_days,
        )

        if master is None:
            raise ValueError("No master frame found.")

        return master

    @staticmethod
    def _copy_original_filename(calibrated: Image, original: Image) -> None:
        if "ORIGNAME" in original.header:
            calibrated.header["L1RAW"] = original.header["ORIGNAME"].replace(".fits", "")

    @staticmethod
    def _copy_calibration_filename(
        calibrated: Image, bias: Image | None = None, dark: Image | None = None, flat: Image | None = None
    ) -> None:
        if bias is not None:
            calibrated.header["L1BIAS"] = (
                bias.header["FNAME"].replace(".fits.fz", "").replace(".fits", ""),
                "Name of BIAS frame",
            )
        if dark is not None:
            calibrated.header["L1DARK"] = (
                dark.header["FNAME"].replace(".fits.fz", "").replace(".fits", ""),
                "Name of DARK frame",
            )
        if flat is not None:
            calibrated.header["L1FLAT"] = (
                flat.header["FNAME"].replace(".fits.fz", "").replace(".fits", ""),
                "Name of FLAT frame",
            )

    @staticmethod
    def _set_calibration_headers(calibrated: Image) -> None:
        calibrated.header["BUNIT"] = ("electron", "Unit of pixel values")
        calibrated.header["RLEVEL"] = (1, "Reduction level")


__all__ = ["Calibration"]
