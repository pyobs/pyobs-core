import numpy as np
from numpy.typing import NDArray

from .combinestack import BlockResult, CombineStack


class SumStack(CombineStack):
    """Combine a stack cube into one frame via the sum of all frames, ignoring NaNs.

    EXPTIME of the result is the total exposure time of all frames.
    """

    __module__ = "pyobs.images.processors.stack"

    method = "sum"

    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        return BlockResult(
            value=np.nansum(block, axis=0, dtype=np.float64),
            n=self._count_valid(block),
            std=np.nanstd(block, axis=0, ddof=1, dtype=np.float64) if need_std else None,
        )

    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        return std * np.sqrt(n)

    def _exptime(self, exptime: float, total: float | None) -> float:
        return exptime if total is None else total


__all__ = ["SumStack"]
