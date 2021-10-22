import logging
from typing import Any, Optional

from pyobs.images import Image
from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processor import ImageProcessor


log = logging.getLogger(__name__)


class ExpTimeEstimator(ImageProcessor):
    """Estimate exposure time."""
    __module__ = 'pyobs.images.processors.exptime'

    def __init__(self, min_exp_time: float = 0., max_exp_time: Optional[float] = None, **kwargs: Any):
        """Init new exposure time estimator."""
        ImageProcessor.__init__(self, **kwargs)
        self._min_exp_time = min_exp_time
        self._max_exp_time = max_exp_time

    def __call__(self, image: Image) -> Image:
        """Processes an image and stores new exposure time in exp_time attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.
        """
        raise NotImplementedError

    def _set_exp_time(self, image: Image, exp_time: float) -> None:
        """Internal setter for exposure time."""

        # min exp time
        if self._min_exp_time is not None and exp_time < self._min_exp_time:
            exp_time = self._min_exp_time

        # max exp time
        if self._max_exp_time is not None and exp_time > self._max_exp_time:
            exp_time = self._max_exp_time

        # set it
        image.set_meta(ExpTime(exp_time))


__all__ = ['ExpTimeEstimator']
