from typing import Union, Optional, Tuple, Any, Dict, cast
import logging

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.images.processors.misc.calibration._calibration_cache import _CalibrationCache
from pyobs.images.processors.misc.calibration._ccddata_calibrator import _CCDDataCalibrator
from pyobs.object import get_object
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class Calibration(ImageProcessor):
    """Calibrate an image."""

    __module__ = "pyobs.images.processors.misc"

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
