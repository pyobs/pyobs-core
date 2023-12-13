import asyncio
from typing import Any
import logging
import numpy as np

from .photometry import Photometry
from pyobs.images import Image

log = logging.getLogger(__name__)


class SepPhotometry(Photometry):
    """Perform photometry using SEP."""

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
        return await loop.run_in_executor(None, SepPhotometry._photometry, image)

    @staticmethod
    def _photometry(image: Image) -> Image:
        import sep
        from pyobs.images.processors.detection import SepSourceDetection

        # check data
        if image.data is None:
            log.warning("No data found in image.")
            return image
        if image.catalog is None:
            log.warning("No catalog found in image.")
            return image

        # no mask?
        mask = image.mask if image.mask is not None else np.zeros(image.data.shape, dtype=bool)

        # remove background
        data, bkg = SepSourceDetection.remove_background(image.data, mask)

        # fetch catalog
        sources = image.catalog.copy()

        # match SEP conventions
        x, y = sources["x"] - 1, sources["y"] - 1

        # get gain
        gain = image.header["DET-GAIN"] if "DET-GAIN" in image.header else None

        # perform aperture photometry for diameters of 1" to 8"
        for diameter in [1, 2, 3, 4, 5, 6, 7, 8]:
            if image.pixel_scale is not None:
                flux, fluxerr, flag = sep.sum_circle(
                    data, x, y, diameter / 2.0 / image.pixel_scale, mask=image.mask, err=image.uncertainty, gain=gain
                )
                sources["fluxaper{0}".format(diameter)] = flux
                sources["fluxerr{0}".format(diameter)] = fluxerr

            else:
                sources["fluxaper{0}".format(diameter)] = 0
                sources["fluxerr{0}".format(diameter)] = 0

        # average background at each source
        # since SEP sums up whole pixels, we need to do the same on an image of ones for the background_area
        bkgflux, fluxerr, flag = sep.sum_ellipse(
            bkg.back(), x, y, sources["a"], sources["b"], np.pi / 2.0, 2.5 * sources["kronrad"], subpix=1
        )
        background_area, _, _ = sep.sum_ellipse(
            np.ones(shape=bkg.back().shape),
            x,
            y,
            sources["a"],
            sources["b"],
            np.pi / 2.0,
            2.5 * sources["kronrad"],
            subpix=1,
        )
        sources["background"] = bkgflux
        sources["background"][background_area > 0] /= background_area[background_area > 0]

        # pick columns for catalog
        new_columns = [
            "fluxaper1",
            "fluxerr1",
            "fluxaper2",
            "fluxerr2",
            "fluxaper3",
            "fluxerr3",
            "fluxaper4",
            "fluxerr4",
            "fluxaper5",
            "fluxerr5",
            "fluxaper6",
            "fluxerr6",
            "fluxaper7",
            "fluxerr7",
            "fluxaper8",
            "fluxerr8",
            "background",
        ]
        cat = sources[image.catalog.colnames + new_columns]

        # copy image, set catalog and return it
        img = image.copy()
        img.catalog = cat
        return img


__all__ = ["SepPhotometry"]
