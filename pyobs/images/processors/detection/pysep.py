import asyncio
import logging
from functools import partial
from typing import Tuple, TYPE_CHECKING, Any, Optional

import numpy as np
import numpy.typing as npt

from pyobs.images import Image
from ._pysep_catalog import PySepCatalog
from .sourcedetection import SourceDetection

if TYPE_CHECKING:
    from sep import Background

log = logging.getLogger(__name__)


class SepSourceDetection(SourceDetection):
    """Detect sources using SEP."""

    __module__ = "pyobs.images.processors.detection"

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

        if image.data is None:
            log.warning("No data found in image.")
            return image

        mask = self._get_mask_or_default(image)

        data, bkg = self.remove_background(image.data, mask)

        sources = await self._extract_sources(data, bkg, mask)

        source_catalog = PySepCatalog.from_array(sources)

        source_catalog.filter_detection_flag()
        source_catalog.clip_rotation_angle()

        source_catalog.calc_ellipticity()
        source_catalog.calc_fwhm()
        source_catalog.calc_kron_radius(data)

        gain = self._get_gain_or_default(image)
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, source_catalog.calc_flux, data, mask, gain)

        source_catalog.calc_flux_radii(data)
        source_catalog.calc_winpos(data)

        source_catalog.rotation_angle_to_degree()
        source_catalog.filter_detection_flag()
        source_catalog.apply_fits_origin_convention()

        output_image = source_catalog.save_to_image(image)
        return output_image

    @staticmethod
    def _get_mask_or_default(image: Image) -> np.ndarray:
        if image.mask is not None:
            return image.mask

        return np.zeros(image.data.shape, dtype=bool)

    @staticmethod
    def _get_gain_or_default(image: Image) -> Optional[float]:
        if "DET-GAIN" in image.header:
            return image.header["DET-GAIN"]

        return None

    @staticmethod
    def remove_background(
        data: npt.NDArray[float], mask: Optional[npt.NDArray[float]] = None
    ) -> Tuple[npt.NDArray[float], "Background"]:
        """Remove background from image in data.

        Args:
            data: Data to remove background from.
            mask: Mask to use for estimating background.

        Returns:
            Image without background.
        """
        import sep

        # get data and make it continuous
        d = data.astype(float)

        # estimate background, probably we need to byte swap
        try:
            bkg = sep.Background(d, mask=mask, bw=32, bh=32, fw=3, fh=3)
        except ValueError as e:
            d = d.byteswap(True).newbyteorder()
            bkg = sep.Background(d, mask=mask, bw=32, bh=32, fw=3, fh=3)

        # subtract it
        bkg.subfrom(d)

        # return data without background and background
        return d, bkg

    async def _extract_sources(self, data, bkg, mask):
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

        return sources


__all__ = ["SepSourceDetection"]
