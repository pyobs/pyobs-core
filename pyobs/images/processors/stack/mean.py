import numpy as np
from numpy.typing import NDArray

from .combinestack import BlockResult, CombineStack


class MeanStack(CombineStack):
    """Combine a stack cube into one frame via the mean of all frames, ignoring NaNs."""

    __module__ = "pyobs.images.processors.stack"

    method = "mean"

    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        return BlockResult(
            value=np.nanmean(block, axis=0, dtype=np.float64),
            n=self._count_valid(block),
            std=np.nanstd(block, axis=0, ddof=1, dtype=np.float64) if need_std else None,
        )

    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        return std / np.sqrt(n)


__all__ = ["MeanStack"]
