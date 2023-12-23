from typing import Tuple

import numpy as np
import numpy.typing as npt
from astropy.stats import SigmaClip

from pyobs.images import Image


class _DaoBackgroundRemover:
    def __init__(self, sigma: float, box_size: Tuple[int, int], filter_size: Tuple[int, int]):
        from photutils.background import MedianBackground

        self._sigma_clip = SigmaClip(sigma=sigma)
        self._box_size = box_size
        self._filter_size = filter_size

        self._bkg_estimator = MedianBackground()

    def __call__(self, image: Image) -> Image:
        background = self._estimate_background(image)
        return self._remove_background(image, background)

    def _estimate_background(self, image: Image) -> npt.NDArray[float]:
        from photutils.background import Background2D

        bkg = Background2D(
            image.data,
            box_size=self._box_size,
            filter_size=self._filter_size,
            sigma_clip=self._sigma_clip,
            bkg_estimator=self._bkg_estimator,
            mask=image.safe_mask,
        )

        return bkg.background

    @staticmethod
    def _remove_background(image: Image, background: npt.NDArray[float]) -> Image:
        output_image = image.copy()
        output_image.data = output_image.data - background
        return output_image
