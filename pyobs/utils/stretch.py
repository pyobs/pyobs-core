"""Stretching image data to 8 bit for display (live view JPEGs, client-side previews)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

StretchFunction = Literal["linear", "sqrt", "asinh", "log"]
CutsMode = Literal["full", "minmax", "percentile", "manual"]

STRETCH_FUNCTIONS: tuple[str, ...] = ("linear", "sqrt", "asinh", "log")
CUTS_MODES: tuple[str, ...] = ("full", "minmax", "percentile", "manual")

# pixels further apart than this (in each axis) are skipped when computing cuts, so that
# percentiles on a large frame stay cheap; a 4x4 subsample is plenty for display cuts
_CUTS_SUBSAMPLE = 4


@dataclass(frozen=True)
class StretchParams:
    """How to map image data to 8 bit."""

    stretch: StretchFunction = "linear"
    """Stretch function applied after the cuts."""

    cuts: CutsMode | None = None
    """How to determine the low/high cuts: ``full`` (the dtype's range, integer data only),
    ``minmax``, ``percentile`` (lo/hi are percentiles) or ``manual`` (lo/hi are data values).
    None picks ``full`` for 8-bit data and ``minmax`` for everything else."""

    lo: float | None = None
    """Low cut: percentile for ``percentile`` (default 0.5), value for ``manual`` (required)."""

    hi: float | None = None
    """High cut: percentile for ``percentile`` (default 99.5), value for ``manual`` (required)."""

    scale: int = 1
    """Downsampling factor (block mean), 1 for none."""

    def __post_init__(self) -> None:
        if self.stretch not in STRETCH_FUNCTIONS:
            raise ValueError(f"Unknown stretch function: {self.stretch}")
        if self.cuts is not None and self.cuts not in CUTS_MODES:
            raise ValueError(f"Unknown cuts mode: {self.cuts}")
        if self.cuts == "manual" and (self.lo is None or self.hi is None):
            raise ValueError("Manual cuts need both lo and hi.")
        if self.cuts == "percentile":
            lo, hi = self.lo if self.lo is not None else 0.5, self.hi if self.hi is not None else 99.5
            if not 0 <= lo < hi <= 100:
                raise ValueError("Percentiles must satisfy 0 <= lo < hi <= 100.")
        if self.scale < 1:
            raise ValueError("Scale must be at least 1.")


def downsample(data: NDArray[Any], factor: int) -> NDArray[Any]:
    """Downsamples the first two axes by a block mean, cropping any remainder.

    Args:
        data: 2D (or 3D with colour as last axis) image.
        factor: Downsampling factor.

    Returns:
        Downsampled data as float32, or the input unchanged for factor 1.
    """
    if factor <= 1:
        return data
    ny, nx = data.shape[0] // factor, data.shape[1] // factor
    if ny == 0 or nx == 0:
        raise ValueError("Downsampling factor is larger than the image.")
    cropped = data[: ny * factor, : nx * factor].astype(np.float32)
    shape = (ny, factor, nx, factor) + cropped.shape[2:]
    return cropped.reshape(shape).mean(axis=(1, 3))


def compute_cuts(data: NDArray[Any], params: StretchParams) -> tuple[float, float]:
    """Computes the low and high cut for the given data.

    Args:
        data: Image data.
        params: Stretch parameters.

    Returns:
        Tuple of (low, high) data values.
    """
    cuts = params.cuts
    if cuts is None:
        cuts = "full" if data.dtype == np.uint8 else "minmax"

    if cuts == "manual":
        return float(params.lo), float(params.hi)  # type: ignore[arg-type]
    if cuts == "full":
        if not np.issubdtype(data.dtype, np.integer):
            raise ValueError("Cuts mode 'full' needs integer data.")
        info = np.iinfo(data.dtype)
        return float(info.min), float(info.max)

    sample = data[::_CUTS_SUBSAMPLE, ::_CUTS_SUBSAMPLE] if data.shape[0] > 256 else data
    sample = sample[np.isfinite(sample)] if np.issubdtype(sample.dtype, np.floating) else sample
    if sample.size == 0:
        return 0.0, 1.0
    if cuts == "minmax":
        return float(np.min(sample)), float(np.max(sample))
    lo = params.lo if params.lo is not None else 0.5
    hi = params.hi if params.hi is not None else 99.5
    low, high = np.percentile(sample, [lo, hi])
    return float(low), float(high)


def stretch_to_uint8(data: NDArray[Any], params: StretchParams | None = None) -> NDArray[np.uint8]:
    """Maps image data to 8 bit for display.

    Colour images (3D, colour as last axis) use the same cuts for all channels.

    Args:
        data: Image data.
        params: Stretch parameters, defaults if None.

    Returns:
        8-bit image.
    """
    params = params if params is not None else StretchParams()
    data = downsample(data, params.scale)

    # fast path: 8-bit data with its full range and a linear stretch is already what we want
    if data.dtype == np.uint8 and params.stretch == "linear" and params.cuts in (None, "full"):
        return data

    low, high = compute_cuts(data, params)
    span = high - low if high > low else 1.0
    x = np.clip((data.astype(np.float32) - low) / span, 0.0, 1.0)

    if params.stretch == "sqrt":
        x = np.sqrt(x)
    elif params.stretch == "asinh":
        x = np.arcsinh(10.0 * x) / np.arcsinh(10.0)
    elif params.stretch == "log":
        x = np.log10(1.0 + 1000.0 * x) / np.log10(1001.0)

    return (x * 255.0 + 0.5).astype(np.uint8)


__all__ = [
    "StretchParams",
    "StretchFunction",
    "CutsMode",
    "STRETCH_FUNCTIONS",
    "CUTS_MODES",
    "downsample",
    "compute_cuts",
    "stretch_to_uint8",
]
