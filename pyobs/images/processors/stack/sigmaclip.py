from typing import Any

import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip
from numpy.typing import NDArray

from .combinestack import BlockResult, CombineStack


class SigmaClipStack(CombineStack):
    """Combine a stack cube into one frame via a kappa-sigma clipped mean.

    Per pixel, values more than sigma standard deviations from the median are rejected
    iteratively (astropy.stats.sigma_clip), then the mean of the remaining values is taken.
    NaNs are rejected as well.
    """

    __module__ = "pyobs.images.processors.stack"

    method = "sigmaclip"

    def __init__(self, sigma: float = 3.0, maxiters: int = 5, **kwargs: Any):
        """Init a new sigma-clipping stack combine step.

        Args:
            sigma: Number of standard deviations used as clipping limit, both sides.
            maxiters: Maximum number of clipping iterations.
        """
        CombineStack.__init__(self, **kwargs)
        if sigma <= 0:
            raise ValueError("sigma must be positive.")
        if maxiters < 1:
            raise ValueError("maxiters must be at least 1.")
        self._sigma = sigma
        self._maxiters = maxiters

    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        clipped = sigma_clip(
            block, sigma=self._sigma, maxiters=self._maxiters, cenfunc="median", stdfunc="std", axis=0, copy=False
        )
        return BlockResult(
            value=np.ma.filled(clipped.mean(axis=0, dtype=np.float64), np.nan),
            n=np.asarray(clipped.count(axis=0)),
            std=np.ma.filled(clipped.std(axis=0, ddof=1, dtype=np.float64), np.nan) if need_std else None,
        )

    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        return std / np.sqrt(n)

    def _add_headers(self, header: fits.Header) -> None:
        header["COMBSIG"] = (self._sigma, "Clipping limit in standard deviations")
        header["COMBITER"] = (self._maxiters, "Maximum number of clipping iterations")


__all__ = ["SigmaClipStack"]
