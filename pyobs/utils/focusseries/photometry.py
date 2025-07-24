from typing import Tuple, Dict, List, Any
import numpy as np
import logging
from pyobs.object import get_object

from pyobs.images.processors.detection import SourceDetection
from pyobs.utils.focusseries.base import FocusSeries
from pyobs.utils.curvefit import fit_hyperbola
from pyobs.images import Image


log = logging.getLogger(__name__)


class PhotometryFocusSeries(FocusSeries):
    """Focus series based on source detection."""

    __module__ = "pyobs.utils.focusseries"

    def __init__(self, source_detection: SourceDetection, radius_column: str = "radius", **kwargs: Any):
        """Initialize a new projection focus series.

        Args:
            source_detection: Photometry to use for estimating PSF sizes
        """

        # stuff
        self._source_detection: SourceDetection = get_object(source_detection, SourceDetection)
        self._radius_col = radius_column
        self._data: List[Dict[str, float]] = []

    def reset(self) -> None:
        """Reset focus series."""
        self._data = []

    async def analyse_image(self, image: Image, focus_value: float) -> None:
        """Analyse given image.

        Args:
            image: Image to analyse
            focus_value: Value to fit along, e.g. focus value or its offset
        """

        # do photometry
        image = await self._source_detection(image)

        # filter
        sources = image.safe_catalog
        if sources is None:
            return
        sources = sources[sources["ellipticity"] < 0.1]
        sources = sources[sources["peak"] > 1000]
        sources = sources[sources["radius"] > 0]

        # calculate median radius
        radius = np.median(sources["radius"])
        radius_err = np.std(sources["radius"])

        # log it
        log.info("Found median radius of %.1f+-%.1f.", radius, radius_err)

        # add to list
        self._data.append({"focus": focus_value, "r": radius, "rerr": radius_err})

    def fit_focus(self) -> Tuple[float, float]:
        """Fit focus from analysed images

        Returns:
            Tuple of new focus and its error
        """

        # get data
        focus = [d["focus"] for d in self._data]
        r = [d["r"] for d in self._data]
        rerr = [d["rerr"] for d in self._data]

        # fit focus
        try:
            foc, err = fit_hyperbola(focus, r, rerr)
        except (RuntimeError, RuntimeWarning):
            raise ValueError("Could not find best focus.")

        # get min and max foci
        min_focus = np.min(focus)
        max_focus = np.max(focus)
        if foc < min_focus or foc > max_focus:
            raise ValueError("New focus out of bounds: {0:.3f}+-{1:.3f}mm.".format(foc, err))

        # return it
        return float(foc), float(err)


__all__ = ["PhotometryFocusSeries"]
