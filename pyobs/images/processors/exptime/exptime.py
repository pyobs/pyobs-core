import logging
from abc import ABCMeta, abstractmethod
from copy import copy
from typing import Any, Optional

import numpy as np

from pyobs.images import Image
from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class ExpTimeEstimator(ImageProcessor, metaclass=ABCMeta):
    """Estimate exposure time."""

    __module__ = "pyobs.images.processors.exptime"

    def __init__(self, min_exp_time: float = 0.0, max_exp_time: Optional[float] = None, **kwargs: Any):
        """Init new exposure time estimator."""
        ImageProcessor.__init__(self, **kwargs)
        self._min_exp_time = min_exp_time
        self._max_exp_time = max_exp_time

    async def __call__(self, image: Image) -> Image:
        """Processes an image and stores new exposure time in exp_time attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.
        """
        nex_exp_time = await self._calc_exp_time(image)
        return self._set_exp_time(image, nex_exp_time)

    @abstractmethod
    async def _calc_exp_time(self, image: Image) -> float:
        """
        Process an image and calculates the new exposure time

        Args:
            image: Image to process.
        """

    def _set_exp_time(self, image: Image, exp_time: float) -> Image:
        """Internal setter for exposure time."""
        output_image = copy(image)
        clipped_exp_time = np.clip(exp_time, self._min_exp_time, self._max_exp_time)
        output_image.set_meta(ExpTime(clipped_exp_time))
        return output_image


__all__ = ["ExpTimeEstimator"]
