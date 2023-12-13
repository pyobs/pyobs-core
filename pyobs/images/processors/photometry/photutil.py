import asyncio
from functools import partial
from typing import Any, Tuple, List, Optional
from astropy.stats import sigma_clipped_stats
import logging
import numpy as np
from astropy.table import QTable
from photutils import CircularAnnulus, CircularAperture, aperture_photometry
from photutils.aperture import CircularMaskMixin, ApertureMask

from .photometry import Photometry
from pyobs.images import Image

log = logging.getLogger(__name__)


class PhotUtilsPhotometry(Photometry):
    """Perform photometry using PhotUtils."""

    __module__ = "pyobs.images.processors.photometry"

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
        """Initializes an aperture photometry based on PhotUtils.

        Args:
            threshold: Threshold pixel value for detection.
            minarea: Minimum number of pixels required for detection.
            deblend_nthresh: Number of thresholds used for object deblending.
            deblend_cont: Minimum contrast ratio used for object deblending.
            clean: Perform cleaning?
            clean_param: Cleaning parameter (see SExtractor manual).
            *args:
            **kwargs:
        """
        Photometry.__init__(self, **kwargs)

        # store
        self.threshold = threshold
        self.minarea = minarea
        self.deblend_nthresh = deblend_nthresh
        self.deblend_cont = deblend_cont
        self.clean = clean
        self.clean_param = clean_param

    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

        Args:
            image: Image to do aperture photometry on.

        Returns:
            Image with attached catalog.
        """

        output_image = image.copy()

        # no pixel scale given?
        if output_image.pixel_scale is None:
            log.warning("No pixel scale provided by image.")
            return image

        # fetch catalog
        if output_image.catalog is None:
            log.warning("No catalog in image.")
            return image

        # get positions
        positions = [(x - 1, y - 1) for x, y in output_image.catalog.iterrows("x", "y")]

        # perform aperture photometry for diameters of 1" to 8"
        for diameter in [1, 2, 3, 4, 5, 6, 7, 8]:
            await self._aperture_photometry(output_image, positions, diameter)

        return output_image

    async def _aperture_photometry(self, image: Image, positions: List[Tuple[float, float]], diameter: int):
        radius = self._calc_aperture_radius_in_px(image, diameter)
        if radius < 1:
            return

        aperture = CircularAperture(positions, r=radius)
        aperture_flux, aperture_error = await self._calc_aperture_flux(image, aperture)

        median_background = self._calc_median_backgrounds(image, positions, radius)
        aperture_background = self._calc_integrated_background(median_background, aperture)

        corrected_aperture = self._background_correct_aperture_flux(aperture_flux, aperture_background)

        self._update_header(image, diameter, corrected_aperture, aperture_error, median_background)


    @staticmethod
    def _calc_aperture_radius_in_px(image: Image, diameter: int):
        radius = diameter / 2.0
        return radius / image.pixel_scale

    def _calc_median_backgrounds(self, image: Image, positions: List[Tuple[float, float]], radius: float) -> np.ndarray[float]:
        annulus_aperture = CircularAnnulus(positions, r_in=2 * radius, r_out=3 * radius)
        annulus_masks = annulus_aperture.to_mask(method="center")

        bkg_median = [
            self._calc_median_background(image, mask)
            for mask in annulus_masks
        ]

        return np.array(bkg_median)

    @staticmethod
    def _calc_median_background(image: Image, mask: ApertureMask) -> float:
        annulus_data = mask.multiply(image.data)
        annulus_data_1d = annulus_data[mask.data > 0]
        _, sigma_clipped_median, _ = sigma_clipped_stats(annulus_data_1d)
        return sigma_clipped_median

    @staticmethod
    def _calc_integrated_background(median_background: np.ndarray[float], aperture: CircularAperture) -> np.ndarray[float]:
        return median_background * aperture.area

    @staticmethod
    async def _calc_aperture_flux(image: Image, aperture: CircularAperture) -> Tuple[np.ndarray[float], Optional[np.ndarray[float]]]:
        loop = asyncio.get_running_loop()
        phot: QTable = await loop.run_in_executor(
            None, partial(aperture_photometry, image.data, aperture, mask=image.mask, error=image.uncertainty)
        )
        aperture_flux = phot["aperture_sum"]
        aperture_error = phot["aperture_sum_err"] if "aperture_sum_err" in phot.keys() else None

        return aperture_flux, aperture_error

    @staticmethod
    def _background_correct_aperture_flux(aperture_flux: np.ndarray[float], aperture_background: np.ndarray[float]) -> np.ndarray[float]:
        return aperture_flux - aperture_background

    @staticmethod
    def _update_header(image: Image, diameter: int, corrected_aperture_flux: np.ndarray[float], aperture_error: Optional[np.ndarray[float]], median_background: np.ndarray[float]):
        image.catalog["fluxaper%d" % diameter] = corrected_aperture_flux
        if aperture_error is not None:
            image.catalog["fluxerr%d" % diameter] = aperture_error
        image.catalog["bkgaper%d" % diameter] = median_background


__all__ = ["PhotUtilsPhotometry"]
