import asyncio
from functools import partial
from typing import Union, Optional, List, Tuple, Any, Dict, cast
import logging
import astropy.units as u

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
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
    calib_cache: List[Tuple[Tuple[ImageType, str, str, Optional[str]], Image]] = []

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

        # store
        self._max_cache_size = max_cache_size
        self._max_days_bias = max_days_bias
        self._max_days_dark = max_days_dark
        self._max_days_flat = max_days_flat
        self._require_bias = require_bias
        self._require_dark = require_dark
        self._require_flat = require_flat

        # get archive
        self._archive = get_object(archive, Archive)

    async def __call__(self, image: Image) -> Image:
        """Calibrate an image.

        Args:
            image: Image to calibrate.

        Returns:
            Calibrated image.
        """
        import ccdproc

        # get calibration masters
        try:
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
        except ValueError as e:
            log.warning("Could not find calibration frames: " + str(e))
            return image

        # trim image
        ccddata = Pipeline.trim_ccddata(image.to_ccddata())

        # calibrate image
        c = ccdproc.ccd_process(
            ccddata,
            error=True,
            master_bias=bias.to_ccddata() if bias is not None else None,
            dark_frame=dark.to_ccddata() if dark is not None else None,
            master_flat=flat.to_ccddata() if flat is not None else None,
            bad_pixel_mask=None,
            gain=image.header["DET-GAIN"] * u.electron / u.adu,
            readnoise=image.header["DET-RON"] * u.electron,
            dark_exposure=dark.header["EXPTIME"] * u.second if dark is not None else None,
            data_exposure=image.header["EXPTIME"] * u.second,
            dark_scale=True,
            gain_corrected=False,
        )

        # to image
        calibrated = Image.from_ccddata(c)
        calibrated.header["BUNIT"] = ("electron", "Unit of pixel values")

        # set raw filename
        if "ORIGNAME" in image.header:
            calibrated.header["L1RAW"] = image.header["ORIGNAME"].replace(".fits", "")

        # add calibration frames
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

        # set RLEVEL
        calibrated.header["RLEVEL"] = (1, "Reduction level")

        # finished
        return calibrated

    async def _find_master(
        self, image: Image, image_type: ImageType, max_days: Optional[float] = None
    ) -> Optional[Image]:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_type: image type.

        Returns:
            Image or None

        Raises:
            ValueError: if no calibration frame could be found.
        """

        # get mode
        try:
            instrument = image.header["INSTRUME"]
            binning = "{0}x{0}".format(image.header["XBINNING"])
            filter_name = cast(str, image.header["FILTER"]) if "FILTER" in image.header else None
            time = Time(image.header["DATE-OBS"])
            mode = image_type, instrument, binning, filter_name
        except KeyError:
            # could not fetch header items
            raise ValueError("Could not fetch items from image header.")

        # is in cache?
        for m, item in Calibration.calib_cache:
            if m == mode:
                return item

        # try to download one
        master = await Pipeline.find_master(
            self._archive,
            image_type,
            time,
            instrument,
            binning,
            None if image_type in [ImageType.BIAS, ImageType.DARK] else filter_name,
            max_days=max_days,
        )

        # nothing?
        if master is None:
            raise ValueError("No master frame found.")

        # store it in cache
        Calibration.calib_cache.append((mode, master))

        # too many entries?
        while len(Calibration.calib_cache) > self._max_cache_size:
            Calibration.calib_cache.pop(0)

        # return it
        return master


__all__ = ["Calibration"]
