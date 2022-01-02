import asyncio
from functools import partial
from typing import Any
from astropy.stats import sigma_clipped_stats
import logging
import numpy as np
from photutils import CircularAnnulus, CircularAperture, aperture_photometry

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
        loop = asyncio.get_running_loop()

        # no pixel scale given?
        if image.pixel_scale is None:
            log.warning("No pixel scale provided by image.")
            return image

        # fetch catalog
        if image.catalog is None:
            log.warning("No catalog in image.")
            return image
        sources = image.catalog.copy()

        # get positions
        positions = [(x - 1, y - 1) for x, y in sources.iterrows("x", "y")]

        # perform aperture photometry for diameters of 1" to 8"
        for diameter in [1, 2, 3, 4, 5, 6, 7, 8]:
            # extraction radius in pixels
            radius = diameter / 2.0 / image.pixel_scale
            if radius < 1:
                continue

            # defines apertures
            aperture = CircularAperture(positions, r=radius)
            annulus_aperture = CircularAnnulus(positions, r_in=2 * radius, r_out=3 * radius)
            annulus_masks = annulus_aperture.to_mask(method="center")

            # loop annuli
            bkg_median = []
            for m in annulus_masks:
                annulus_data = m.multiply(image.data)
                annulus_data_1d = annulus_data[m.data > 0]
                _, median_sigclip, _ = sigma_clipped_stats(annulus_data_1d)
                bkg_median.append(median_sigclip)

            # do photometry
            phot = await loop.run_in_executor(
                None, partial(aperture_photometry, image.data, aperture, mask=image.mask, error=image.uncertainty)
            )

            # calc flux
            bkg_median_np = np.array(bkg_median)
            aper_bkg = bkg_median_np * aperture.area
            sources["fluxaper%d" % diameter] = phot["aperture_sum"] - aper_bkg
            if "aperture_sum_err" in phot.columns:
                sources["fluxerr%d" % diameter] = phot["aperture_sum_err"]
            sources["bkgaper%d" % diameter] = bkg_median_np

        # copy image, set catalog and return it
        img = image.copy()
        img.catalog = sources
        return img


__all__ = ["PhotUtilsPhotometry"]
