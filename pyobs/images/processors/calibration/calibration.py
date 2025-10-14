from typing import Union, Optional, Tuple, Any, Dict, cast
import logging

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors.calibration._calibration_cache import _CalibrationCache
from pyobs.images.processors.calibration._ccddata_calibrator import _CCDDataCalibrator
from pyobs.object import get_object
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class Calibration(ImageProcessor):
    """
    Calibrate an image using master bias, dark, and flat frames fetched from an archive.

    This processor locates appropriate master calibration frames
    (bias, dark, flat) based on the input image metadata, applies calibration to the
    image, and annotates the FITS header with provenance and reduction information.
    Calibration frames are looked up via an :class:`pyobs.archive.Archive` and are
    cached in a class-wide cache to reduce repeated lookups. If required calibration
    frames cannot be found, the original image is returned unchanged.

    :param dict | Archive archive: Archive configuration or an already constructed
                                  :class:`pyobs.archive.Archive` instance used to
                                  locate master calibration frames. If a dictionary
                                  is provided, it is instantiated via
                                  :func:`pyobs.utils.classes.get_object`.
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
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Verifies required image header keys before searching: ``INSTRUME``, ``XBINNING``,
      and ``DATE-OBS`` must be present.
    - Attempts to retrieve required masters (bias, dark, flat) from a class-wide cache.
      On cache miss, queries the configured archive via
      :meth:`pyobs.pipeline.Pipeline.find_master`, matching:

      - Instrument: exact value of ``INSTRUME``.
      - Binning: string formatted as ``"{XBINNING}x{XBINNING}"`` (square binning assumed).
      - Filter: ``FILTER`` only for flats; biases and darks ignore filter.
      - Time constraint: centered on the image ``DATE-OBS`` with optional ``max_days_*``.

    - If any required master is missing, logs a warning and returns the original image
      unchanged.
    - Applies calibration using :class:`pyobs.images.processors.calibration._CCDDataCalibrator`
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
        archive: Union[Dict[str, Any], Archive],
        max_cache_size: int = 20,
        require_bias: bool = True,
        require_dark: bool = True,
        require_flat: bool = True,
        max_days_bias: Optional[float] = None,
        max_days_dark: Optional[float] = None,
        max_days_flat: Optional[float] = None,
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

        self._archive = get_object(archive, Archive)

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
            bias, dark, flat = await self._get_calibrations_masters(image)
        except ValueError as e:
            log.warning("Could not find calibration frames: " + str(e))
            return image

        calibrator = _CCDDataCalibrator(image, bias, dark, flat)
        calibrated = calibrator()

        self._copy_original_filename(calibrated, image)
        self._copy_calibration_filename(calibrated, bias, dark, flat)

        self._set_calibration_headers(calibrated)

        return calibrated

    async def _get_calibrations_masters(self, image: Image) -> Tuple[Optional[Image], Optional[Image], Optional[Image]]:
        bias = (
            None
            if not self._require_bias
            else await self._find_master(image, ImageType.BIAS, max_days=self._max_days_bias)
        )
        dark = (
            None
            if not self._require_dark
            else await self._find_master(image, ImageType.DARK, max_days=self._max_days_dark)
        )
        flat = (
            None
            if not self._require_flat
            else await self._find_master(image, ImageType.SKYFLAT, max_days=self._max_days_flat)
        )

        return bias, dark, flat

    async def _find_master(self, image: Image, image_type: ImageType, max_days: Optional[float] = None) -> Image:
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

        if not (has_instrument and has_binning and has_time):
            raise ValueError("Could not fetch items from image header.")

    async def _find_master_in_archive(
        self, image: Image, image_type: ImageType, max_days: Optional[float] = None
    ) -> Image:
        instrument = image.header["INSTRUME"]
        binning = "{0}x{0}".format(image.header["XBINNING"])
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
