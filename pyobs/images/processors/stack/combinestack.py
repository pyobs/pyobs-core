import asyncio
import logging
import warnings
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np
from astropy.io import fits
from numpy.typing import NDArray

from pyobs.images import Image
from pyobs.images.processor import ImageProcessor

log = logging.getLogger(__name__)

# header keywords describing axis 3 of a stack cube, removed after combining
_AXIS3_KEYWORDS = ("CTYPE3", "NAXIS3", "CRPIX3", "CRVAL3", "CDELT3", "CUNIT3")


@dataclass
class BlockResult:
    """Result of combining one block of rows of a stack cube, one entry per pixel.

    Attributes:
        value: Combined value.
        n: Number of valid (non-NaN, non-clipped) values that went into it.
        std: Standard deviation (ddof=1) of those values, or None if not requested.
    """

    value: NDArray[np.float64]
    n: NDArray[np.int_]
    std: NDArray[np.float64] | None = None


class CombineStack(ImageProcessor, metaclass=ABCMeta):
    """Base class for processors that collapse a stack cube from IDataStack.grab_stack() into one frame.

    Only images with 3D data and CTYPE3 = 'FRAME' are combined, everything else (single frames,
    color images) passes through unchanged, so the same pipeline can run on grab_data() and
    grab_stack() products. The result is a 2D float32 frame. The cube is processed in blocks of
    rows in a worker thread, so memory stays bounded and the event loop stays responsive.

    See specs/design/combinestack.md.
    """

    __module__ = "pyobs.images.processors.stack"

    method: ClassVar[str]

    def __init__(self, uncertainty: bool = False, mask: bool = False, chunk_bytes: int = 256 * 1024**2, **kwargs: Any):
        """Init a new stack combine step.

        Args:
            uncertainty: Whether to write the per-pixel uncertainty of the combined value, estimated
                from the scatter between frames, as UNCERT extension.
            mask: Whether to write a MASK extension, flagging pixels without any valid value.
            chunk_bytes: Size of the float32 copy of one block of rows, in bytes. Bounds the memory
                used while combining.
        """
        ImageProcessor.__init__(self, **kwargs)
        if chunk_bytes < 1:
            raise ValueError("chunk_bytes must be positive.")
        self._write_uncertainty = uncertainty
        self._write_mask = mask
        self._chunk_bytes = chunk_bytes

    async def __call__(self, image: Image) -> Image:
        """Combine a stack cube into one frame.

        Args:
            image: Stack cube to combine.

        Returns:
            Combined frame, or the unchanged image if it's not a stack cube.
        """
        if image.safe_data is None:
            log.warning("No data found in image.")
            return image
        if image.data.ndim != 3 or image.header.get("CTYPE3") != "FRAME":
            return image

        count = image.data.shape[0]
        log.info("Combining stack of %d frames (%s)...", count, self.method)
        loop = asyncio.get_running_loop()
        value, uncertainty, mask = await loop.run_in_executor(None, self._combine, image.data)

        header = image.header.copy()
        for key in _AXIS3_KEYWORDS:
            if key in header:
                del header[key]
        if "NAXIS" in header:
            header["NAXIS"] = 2
        header["COMBMETH"] = (self.method, "Method used to combine the stack")

        exptime = header.get("EXPTIME")
        frames = image.safe_frames
        total: float | None = None
        if frames is not None and "EXPTIME" in frames.colnames and len(frames) > 0:
            total = float(np.sum(frames["EXPTIME"]))
        elif exptime is not None:
            total = count * float(exptime)
        if total is not None:
            header["TEXPTIME"] = (total, "Total exposure time of all frames [s]")
        if exptime is not None:
            header["EXPTIME"] = self._exptime(float(exptime), total)
        self._add_headers(header)

        return Image(value, header=header, uncertainty=uncertainty, mask=mask, frames=frames, meta=image.meta)

    def _combine(
        self, cube: NDArray[Any]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32] | None, NDArray[Any] | None]:
        """Combine the cube block by block. Runs in a worker thread.

        Args:
            cube: Stack cube (count, ny, nx).

        Returns:
            Tuple of combined data, uncertainty (or None), and boolean mask (or None).
        """
        count, ny, nx = cube.shape
        rows = max(1, self._chunk_bytes // (count * nx * 4))

        value = np.empty((ny, nx), dtype=np.float32)
        uncertainty = np.empty((ny, nx), dtype=np.float32) if self._write_uncertainty else None
        mask = np.empty((ny, nx), dtype=np.bool_) if self._write_mask else None

        for y0 in range(0, ny, rows):
            y1 = min(ny, y0 + rows)
            block = cube[:, y0:y1, :].astype(np.float32)

            # all-NaN pixels warn in nanmean/nanmedian/nanstd and sigma_clip, the NaN is intended
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = self._combine_block(block, self._write_uncertainty)

                # np.nansum returns 0 for an all-NaN pixel, so set those explicitly for every method
                empty = result.n == 0
                value[y0:y1] = np.where(empty, np.nan, result.value)

                if uncertainty is not None:
                    if result.std is None:
                        raise RuntimeError(f"{type(self).__name__} did not return std.")
                    unc = self._uncertainty(result.std, result.n)
                    uncertainty[y0:y1] = np.where(result.n < 2, np.nan, unc)

            if mask is not None:
                mask[y0:y1] = empty

        return value, uncertainty, mask

    @staticmethod
    def _count_valid(block: NDArray[np.float32]) -> NDArray[np.int_]:
        """Number of non-NaN values per pixel along axis 0."""
        return np.count_nonzero(~np.isnan(block), axis=0)

    @abstractmethod
    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        """Combine one block of rows along axis 0. Runs in a worker thread.

        Args:
            block: Block of the cube (count, rows, nx), a float32 copy that may be modified.
            need_std: Whether BlockResult.std is needed (uncertainty requested).

        Returns:
            Combined values, number of valid values, and standard deviation per pixel.
        """
        ...

    @abstractmethod
    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        """Uncertainty of the combined value from the scatter of the frames.

        Args:
            std: Standard deviation (ddof=1) of the valid values per pixel.
            n: Number of valid values per pixel.

        Returns:
            Uncertainty per pixel. Pixels with n < 2 are set to NaN by the caller.
        """
        ...

    def _exptime(self, exptime: float, total: float | None) -> float:
        """EXPTIME of the combined frame. Default: per-frame exposure time, unchanged.

        Args:
            exptime: Per-frame exposure time.
            total: Total exposure time of all frames, if known.

        Returns:
            New EXPTIME.
        """
        return exptime

    def _add_headers(self, header: fits.Header) -> None:
        """Add method-specific FITS headers. Default: none.

        Args:
            header: Header of the combined frame.
        """
        pass


__all__ = ["BlockResult", "CombineStack"]
