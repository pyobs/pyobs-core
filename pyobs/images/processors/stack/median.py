import numpy as np
from numpy.typing import NDArray

from .combinestack import BlockResult, CombineStack

# sqrt(pi/2): standard error of the median relative to that of the mean, asymptotic for Gaussian noise
_MEDIAN_ERROR_FACTOR = float(np.sqrt(np.pi / 2.0))


class MedianStack(CombineStack):
    """Combine a stack cube into one frame via the median of all frames, ignoring NaNs."""

    __module__ = "pyobs.images.processors.stack"

    method = "median"

    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        # std and n first, the median may reorder the block in place
        std = np.nanstd(block, axis=0, ddof=1, dtype=np.float64) if need_std else None
        n = self._count_valid(block)
        value = np.nanmedian(block, axis=0, overwrite_input=True).astype(np.float64)
        return BlockResult(value=value, n=n, std=std)

    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        return _MEDIAN_ERROR_FACTOR * std / np.sqrt(n)


__all__ = ["MedianStack"]
