import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Optional, cast
import numpy as np
import numpy.typing as npt

from pyobs.images import Image
from ._pysep_stats_calculator import PySepStatsCalculator
from ._source_catalog import _SourceCatalog
from .sourcedetection import SourceDetection

if TYPE_CHECKING:
    from sep import Background

log = logging.getLogger(__name__)


class SepSourceDetection(SourceDetection):
    """Detect sources using SEP."""

    __module__ = "pyobs.images.processors.detection"

    _CATALOG_KEYS = [
        "x",
        "y",
        "peak",
        "flux",
        "fwhm",
        "a",
        "b",
        "theta",
        "ellipticity",
        "tnpix",
        "kronrad",
        "fluxrad25",
        "fluxrad50",
        "fluxrad75",
        "xwin",
        "ywin",
    ]

    def __init__(
        self,
        threshold: float = 1.5,
        minarea: int = 5,
        deblend_nthresh: int = 32,
        deblend_cont: float = 0.005,
        clean: bool = True,
        clean_param: float = 1.0,
        **kwargs: Any,
    ):
        """Initializes a wrapper for SEP. See its documentation for details.

        Highly inspired by LCO's wrapper for SEP, see:
        https://github.com/LCOGT/banzai/blob/master/banzai/photometry.py

        Args:
            threshold: Threshold pixel value for detection.
            minarea: Minimum number of pixels required for detection.
            deblend_nthresh: Number of thresholds used for object deblending.
            deblend_cont: Minimum contrast ratio used for object deblending.
            clean: Perform cleaning?
            clean_param: Cleaning parameter (see SExtractor manual).
        """
        SourceDetection.__init__(self, **kwargs)

        self.threshold = threshold
        self.minarea = minarea
        self.deblend_nthresh = deblend_nthresh
        self.deblend_cont = deblend_cont
        self.clean = clean
        self.clean_param = clean_param

    async def __call__(self, image: Image) -> Image:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Image with attached catalog.
        """

        if image.safe_data is None:
            log.warning("No data found in image.")
            return image

        mask = self._get_mask_or_default(image)

        data, background = self.remove_background(image.data, mask)

        sources = await self._extract_sources(data, background, mask)

        source_catalog = _SourceCatalog.from_array(sources)
        source_catalog.filter_detection_flag()

        gain = self._get_gain_or_default(image)
        sep_calculator = PySepStatsCalculator(source_catalog, data, mask, gain)
        source_catalog = await sep_calculator()

        source_catalog.filter_detection_flag()
        source_catalog.wrap_rotation_angle_at_ninty_deg()
        source_catalog.rotation_angle_to_degree()
        source_catalog.apply_fits_origin_convention()

        output_image = source_catalog.save_to_image(image, self._CATALOG_KEYS)
        return output_image

    @staticmethod
    def _get_mask_or_default(image: Image) -> npt.NDArray[np.floating[Any]]:
        return image.mask if image.safe_mask is not None else np.zeros(image.data.shape, dtype=bool)

    @staticmethod
    def _get_gain_or_default(image: Image) -> Optional[float]:
        if "DET-GAIN" in image.header:
            return cast(float, image.header["DET-GAIN"])

        return None

    @staticmethod
    def remove_background(
        data: npt.NDArray[np.floating[Any]],
        mask: npt.NDArray[np.floating[Any]] | None = None,
    ) -> tuple[npt.NDArray[np.floating[Any]], "Background"]:
        """Remove background from image in data.

        Args:
            data: Data to remove background from.
            mask: Mask to use for estimating background.

        Returns:
            Image without background, Background
        """
        import sep

        continuous_data = data.astype(float)

        try:
            background = sep.Background(continuous_data, mask=mask, bw=32, bh=32, fw=3, fh=3)
        except ValueError:
            d = continuous_data.byteswap(True).newbyteorder()
            background = sep.Background(d, mask=mask, bw=32, bh=32, fw=3, fh=3)

        background.subfrom(continuous_data)

        return continuous_data, background

    async def _extract_sources(
        self,
        data: npt.NDArray[np.floating[Any]],
        bkg: "Background",
        mask: npt.NDArray[np.floating[Any]],
    ) -> npt.NDArray[Any]:
        import sep

        loop = asyncio.get_running_loop()
        sources = await loop.run_in_executor(
            None,
            partial(
                sep.extract,
                data,
                self.threshold,
                err=bkg.globalrms,
                minarea=self.minarea,
                deblend_nthresh=self.deblend_nthresh,
                deblend_cont=self.deblend_cont,
                clean=self.clean,
                clean_param=self.clean_param,
                mask=mask,
            ),
        )

        return cast(npt.NDArray[Any], sources)


__all__ = ["SepSourceDetection"]
