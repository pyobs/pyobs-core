import logging
import re
from typing import Any, cast
import numpy as np
import numpy.typing as npt
from scipy.interpolate import UnivariateSpline
from scipy.optimize import fmin

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class ProjectedOffsets(Offsets):
    """
    Compute pixel offsets for guiding by correlating 1D projections of the current image with a reference frame.

    This asynchronous processor implements an auto-guiding method based on collapsing
    images along the x and y axes and cross-correlating these 1D profiles against a
    stored reference. On the first invocation, it initializes by storing the reference
    projections from the input image and returns. On subsequent calls, it computes the
    current projections, performs background (sky) subtraction, estimates sub-pixel
    shifts via cross-correlation and Gaussian peak fitting, and stores the resulting
    PixelOffsets(dx, dy) in the image metadata. Pixel data and FITS headers are not
    modified.

    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Reference initialization:
      - If no reference is set, processes the input image to obtain sky-subtracted
        1D projections along x and y, stores them as the reference, and returns.
    - Per-image guiding update:
      - Processes the current image to obtain sky-subtracted 1D projections.
      - Computes dx and dy by cross-correlating current vs. reference projections
        and fitting a Gaussian to the correlation peak within a small window to obtain
        sub-pixel offsets.
      - If either axis fails to produce a valid offset, logs a warning and returns
        the image unchanged.
      - Otherwise, attaches PixelOffsets(dx, dy) to image metadata.
    - Cropping via TRIMSEC:
      - If the FITS header contains TRIMSEC in the form "[x0:x1,y0:y1]" (1-based, inclusive),
        the image is cropped to that rectangle before projection.
    - Projection and sky subtraction:
      - Collapses the image by summing rows and columns with NaN-safe summation.
      - Subtracts a smooth sky continuum from each 1D projection:
        - Divides the projection into sbin=10 bins.
        - For each bin, estimates the continuum level as the median of the upper
          fraction (frac=0.15) of values.
        - Fits a spline (UnivariateSpline) through these bin medians and subtracts
          the fitted continuum from the projection.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with 2D pixel data; optional TRIMSEC header
      for cropping prior to projection.
    - Output: :class:`pyobs.images.Image` with PixelOffsets(dx, dy) set in metadata
      after the reference is initialized; otherwise unchanged.

    Configuration (YAML)
    --------------------
    Initialize on first frame, then report offsets on subsequent frames:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.ProjectedOffsets

    Notes
    -----
    - Offset sign convention: positive dx indicates that the current image’s x-profile
      is shifted to larger pixel indices relative to the reference; similarly for dy.
      Ensure this matches the downstream module that applies the offsets.
    - The Gaussian fit is performed around the cross-correlation peak within a window
      of width fit_width=10 by default; failed fits or peaks outside the window result
      in no offset update.
    - Sky subtraction parameters (frac=0.15, sbin=10) are fixed in this implementation;
      adjust the code if your background structure requires different settings.
    - Call reset() to clear the stored reference projections and reinitialize on the
      next image.
    """

    __module__ = "pyobs.images.processors.offsets"

    def __init__(self, **kwargs: Any):
        """Initializes a new auto guiding system."""
        Offsets.__init__(self, **kwargs)

        # init
        self._ref_image: tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]] | None = None

    async def reset(self) -> None:
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self._ref_image = None

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        if not self._reference_initialized():
            log.info("Initialising auto-guiding with new image...")
            self._ref_image = self._process(image)
            return image

        log.info("Perform auto-guiding on new image...")
        sum_x, sum_y = self._process(image)

        if self._ref_image is None:
            raise ValueError("No reference image.")
        dx = self._calc_1d_offset(sum_x, self._ref_image[0])
        dy = self._calc_1d_offset(sum_y, self._ref_image[1])
        if dx is None or dy is None:
            log.warning("Could not correlate peaks.")
            return image

        image.set_meta(PixelOffsets(dx, dy))
        return image

    def _reference_initialized(self) -> bool:
        return self._ref_image is not None

    @staticmethod
    def _process(
        image: Image,
    ) -> tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]]:
        """Project image along x and y axes and return results.

        Args:
            image: Image to process.

        Returns:
            Projected images.
        """

        # get image data and header
        data, hdr = image.data, image.header

        # trimsec
        if "TRIMSEC" in hdr:
            m = re.match(r"\[([0-9]+):([0-9]+),([0-9]+):([0-9]+)\]", hdr["TRIMSEC"])
            if m is None:
                raise ValueError("Invalid trimsec.")
            x0, x1, y0, y1 = [int(f) for f in m.groups()]
            data = data[y0 - 1 : y1, x0 - 1 : x1]

        # collapse
        sum_x = np.nansum(data, 0)
        sum_y = np.nansum(data, 1)

        # sky subtraction
        return ProjectedOffsets._subtract_sky(sum_x), ProjectedOffsets._subtract_sky(sum_y)

    @staticmethod
    def _subtract_sky(
        data: npt.NDArray[np.floating[Any]], frac: float = 0.15, sbin: int = 10
    ) -> npt.NDArray[np.floating[Any]]:
        # find continuum for every of the sbin bins
        bins = np.zeros((sbin,))
        binxs = np.zeros((sbin,))
        x = list(range(len(data)))
        w1 = 0.0
        w2 = float(len(x)) / sbin
        for i in range(sbin):
            # sort data in range
            bindata = list(reversed(sorted(data[int(w1) : int(w2)].tolist())))
            # calculate median and set wavelength
            bins[i] = np.median(bindata[int(-frac * len(bindata)) : -1])
            binxs[i] = np.mean(x[int(w1) : int(w2)])
            # reset ranges
            w1 = w2
            w2 += float(len(x)) / sbin
            # check for last bin
            if i == sbin - 1:
                w2 = len(x)

        # fit it
        w = np.where(~np.isnan(bins))
        ip = UnivariateSpline(binxs[w], bins[w])
        cont = ip(x)

        # return continuum
        return cast(npt.NDArray[np.floating[Any]], data - cont)

    @staticmethod
    def _calc_1d_offset(
        data1: npt.NDArray[np.floating[Any]], data2: npt.NDArray[np.floating[Any]], fit_width: int = 10
    ) -> float | None:
        # do cross-correlation
        corr = np.correlate(data1, data2, "full")

        # find index of maximum
        i_max = np.argmax(corr)
        centre = i_max - data1.size + 1

        # cut window
        x = np.linspace(centre - fit_width, centre + fit_width, 2 * fit_width + 1)
        y = corr[i_max - fit_width : i_max + fit_width + 1]

        # moment calculation for initial guesses
        total = float(y.sum())
        mean = (x * y).sum() / total
        variance = (x * x * y).sum() / total - mean**2

        # initial guess
        guesses = [np.max(y), mean, variance]

        # perform fit
        result = fmin(ProjectedOffsets._gaussian_fit, guesses, args=(y, x), disp=False)

        # sanity check and finish up
        shift = float(result[1])
        if shift < centre - fit_width or shift > centre + fit_width:
            return None
        return shift

    @staticmethod
    def _gaussian_fit(pars: list[float], y: npt.NDArray[np.floating[Any]], x: npt.NDArray[np.floating[Any]]) -> float:
        err = y - ProjectedOffsets._gaussian(pars, x)
        return float((err * err).sum())

    @staticmethod
    def _gaussian(pars: list[float], x: npt.NDArray[np.floating[Any]]) -> npt.NDArray[np.floating[Any]]:
        a = pars[0]
        x0 = pars[1]
        sigma = pars[2]
        return cast(npt.NDArray[np.floating[Any]], a * np.exp(-((x - x0) ** 2) / (2.0 * sigma**2)))


__all__ = ["ProjectedOffsets"]
