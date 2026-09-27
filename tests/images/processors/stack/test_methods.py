"""Tests for the concrete stack combine methods. See specs/design/combinestack.md."""

from __future__ import annotations

import numpy as np
import pytest
from astropy.stats import sigma_clip

from pyobs.images.processors.stack import MeanStack, MedianStack, SigmaClipStack, SumStack

from .conftest import make_cube


def cube_data() -> np.ndarray:
    rng = np.random.default_rng(1)
    return rng.normal(1000.0, 10.0, size=(9, 5, 4)).astype(np.float32)


@pytest.mark.asyncio
async def test_mean() -> None:
    data = cube_data()
    result = await MeanStack(uncertainty=True)(make_cube(data))
    np.testing.assert_allclose(result.data, data.mean(axis=0, dtype=np.float64), rtol=1e-6)
    np.testing.assert_allclose(result.uncertainty, data.std(axis=0, ddof=1, dtype=np.float64) / 3.0, rtol=1e-5)
    assert result.header["COMBMETH"] == "mean"
    assert result.header["EXPTIME"] == 2.0


@pytest.mark.asyncio
async def test_median() -> None:
    data = cube_data()
    result = await MedianStack(uncertainty=True)(make_cube(data))
    np.testing.assert_allclose(result.data, np.median(data, axis=0), rtol=1e-6)
    expected = np.sqrt(np.pi / 2) * data.std(axis=0, ddof=1, dtype=np.float64) / 3.0
    np.testing.assert_allclose(result.uncertainty, expected, rtol=1e-5)
    assert result.header["COMBMETH"] == "median"
    assert result.header["EXPTIME"] == 2.0


@pytest.mark.asyncio
async def test_sum() -> None:
    data = cube_data()
    result = await SumStack(uncertainty=True)(make_cube(data))
    np.testing.assert_allclose(result.data, data.sum(axis=0, dtype=np.float64), rtol=1e-6)
    np.testing.assert_allclose(result.uncertainty, data.std(axis=0, ddof=1, dtype=np.float64) * 3.0, rtol=1e-5)
    assert result.header["COMBMETH"] == "sum"
    assert result.header["EXPTIME"] == 18.0
    assert result.header["TEXPTIME"] == 18.0


@pytest.mark.asyncio
async def test_sum_of_uint16_is_exact_beyond_float32_accumulation() -> None:
    # 300 saturated frames: 19660500 > 2**24, a float32 accumulator would round
    data = np.full((300, 1, 2), 65535, dtype=np.uint16)
    result = await SumStack()(make_cube(data))
    assert float(result.data[0, 0]) == pytest.approx(300 * 65535, rel=1e-7)


@pytest.mark.asyncio
async def test_nan_ignored() -> None:
    data = np.array([[[1.0]], [[np.nan]], [[3.0]]], dtype=np.float32)
    assert (await MeanStack()(make_cube(data))).data[0, 0] == 2.0
    assert (await MedianStack()(make_cube(data))).data[0, 0] == 2.0
    assert (await SumStack()(make_cube(data))).data[0, 0] == 4.0
    assert (await SigmaClipStack()(make_cube(data))).data[0, 0] == 2.0


@pytest.mark.asyncio
async def test_sigmaclip_rejects_outlier_frame() -> None:
    data = cube_data()
    data[4] += 10000.0  # e.g. a cosmic ray / satellite trail in one frame
    result = await SigmaClipStack(sigma=3.0)(make_cube(data))
    clean = np.delete(data, 4, axis=0)
    np.testing.assert_allclose(result.data, clean.mean(axis=0, dtype=np.float64), rtol=1e-6)


@pytest.mark.asyncio
async def test_sigmaclip_matches_astropy() -> None:
    data = cube_data()
    data[2, 1, 1] = 5000.0
    result = await SigmaClipStack(sigma=2.5, maxiters=3, uncertainty=True)(make_cube(data))
    clipped = sigma_clip(data, sigma=2.5, maxiters=3, cenfunc="median", stdfunc="std", axis=0)
    np.testing.assert_allclose(result.data, clipped.mean(axis=0).filled(np.nan), rtol=1e-6)
    expected = clipped.std(axis=0, ddof=1) / np.sqrt(clipped.count(axis=0))
    np.testing.assert_allclose(result.uncertainty, expected, rtol=1e-5)


@pytest.mark.asyncio
async def test_sigmaclip_headers() -> None:
    result = await SigmaClipStack(sigma=2.5, maxiters=3)(make_cube(cube_data()))
    assert result.header["COMBMETH"] == "sigmaclip"
    assert result.header["COMBSIG"] == 2.5
    assert result.header["COMBITER"] == 3
    assert result.header["EXPTIME"] == 2.0


def test_sigmaclip_invalid_params() -> None:
    with pytest.raises(ValueError):
        SigmaClipStack(sigma=0.0)
    with pytest.raises(ValueError):
        SigmaClipStack(maxiters=0)
