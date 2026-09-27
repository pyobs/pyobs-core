"""Tests for the CombineStack base class. See specs/design/combinestack.md."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from pyobs.images import Image
from pyobs.images.processors.stack import BlockResult, CombineStack, MeanStack

from .conftest import make_cube


class ZeroSumStack(CombineStack):
    """Test subclass: plain nansum, returns 0 for all-NaN pixels like numpy does."""

    method = "zerosum"

    def _combine_block(self, block: NDArray[np.float32], need_std: bool) -> BlockResult:
        return BlockResult(
            value=np.nansum(block, axis=0, dtype=np.float64),
            n=self._count_valid(block),
            std=np.nanstd(block, axis=0, ddof=1, dtype=np.float64) if need_std else None,
        )

    def _uncertainty(self, std: NDArray[np.float64], n: NDArray[np.int_]) -> NDArray[np.float64]:
        return std


def random_cube(count: int = 5, ny: int = 7, nx: int = 6) -> NDArray[np.uint16]:
    rng = np.random.default_rng(42)
    return rng.integers(0, 60000, size=(count, ny, nx), dtype=np.uint16)


@pytest.mark.asyncio
async def test_2d_frame_passes_through() -> None:
    image = Image(np.ones((4, 5), dtype=np.float32))
    assert await MeanStack()(image) is image


@pytest.mark.asyncio
async def test_color_image_passes_through() -> None:
    image = Image(np.ones((3, 4, 5), dtype=np.float32))
    assert await MeanStack()(image) is image


@pytest.mark.asyncio
async def test_no_data_passes_through() -> None:
    image = Image()
    assert await MeanStack()(image) is image


@pytest.mark.asyncio
async def test_output_is_2d_float32() -> None:
    result = await MeanStack()(make_cube(random_cube()))
    assert result.data.shape == (7, 6)
    assert result.data.dtype == np.float32


@pytest.mark.asyncio
async def test_headers() -> None:
    cube = make_cube(random_cube(count=4), exptime=2.0)
    cube.header["NAXIS"] = 3
    cube.header["CRPIX3"] = 1.0
    result = await MeanStack()(cube)

    for key in ("CTYPE3", "NAXIS3", "CRPIX3"):
        assert key not in result.header
    assert result.header["NAXIS"] == 2
    assert result.header["NAXIS1"] == 6
    assert result.header["NAXIS2"] == 7
    assert result.header["NFRAMES"] == 4
    assert result.header["DATE-OBS"] == cube.header["DATE-OBS"]
    assert result.header["DATE-END"] == cube.header["DATE-END"]
    assert result.header["COMBMETH"] == "mean"
    assert result.header["EXPTIME"] == 2.0
    assert result.header["TEXPTIME"] == 8.0
    assert result.safe_frames is not None
    assert len(result.frames) == 4


@pytest.mark.asyncio
async def test_texptime_from_frames_table() -> None:
    cube = make_cube(random_cube(count=3), exptime=2.0)
    cube.frames["EXPTIME"] = [1.0, 2.0, 4.0]
    result = await MeanStack()(cube)
    assert result.header["TEXPTIME"] == 7.0


@pytest.mark.asyncio
async def test_texptime_fallback_without_frames_table() -> None:
    result = await MeanStack()(make_cube(random_cube(count=3), exptime=2.0, frames=False))
    assert result.header["TEXPTIME"] == 6.0


@pytest.mark.asyncio
async def test_axis3_wcs_keys_removed() -> None:
    cube = make_cube(random_cube())
    for key in ("CROTA3", "CD3_3", "CD1_3", "PC3_1", "PC2_3"):
        cube.header[key] = 0.0
    cube.header["CD1_1"] = 1.0
    cube.header["PC2_2"] = 1.0
    result = await MeanStack()(cube)
    for key in ("CROTA3", "CD3_3", "CD1_3", "PC3_1", "PC2_3"):
        assert key not in result.header
    assert result.header["CD1_1"] == 1.0
    assert result.header["PC2_2"] == 1.0


@pytest.mark.asyncio
async def test_texptime_fallback_on_nan_in_frames_table() -> None:
    cube = make_cube(random_cube(count=3), exptime=2.0)
    cube.frames["EXPTIME"] = [1.0, np.nan, 4.0]
    result = await MeanStack()(cube)
    assert result.header["TEXPTIME"] == 6.0


@pytest.mark.asyncio
async def test_texptime_fallback_on_frames_table_length_mismatch() -> None:
    cube = make_cube(random_cube(count=3), exptime=2.0)
    cube.frames.remove_row(0)
    result = await MeanStack()(cube)
    assert result.header["TEXPTIME"] == 6.0


@pytest.mark.parametrize(
    "chunk_bytes, expected",
    [(1, 1), (6 * (4 * 5 + 40) * 3, 3), (6 * (4 * 5 + 40) * 3 + 1, 3), (10**9, 10**9 // (6 * 60))],
)
def test_rows_per_block_includes_temporaries(chunk_bytes: int, expected: int) -> None:
    assert MeanStack(chunk_bytes=chunk_bytes)._rows_per_block(count=5, nx=6) == expected


@pytest.mark.asyncio
async def test_no_exptime() -> None:
    result = await MeanStack()(make_cube(random_cube(count=3), exptime=None, frames=False))
    assert "EXPTIME" not in result.header
    assert "TEXPTIME" not in result.header


@pytest.mark.asyncio
async def test_meta_kept_and_input_untouched() -> None:
    cube = make_cube(random_cube())
    cube.meta["foo"] = "bar"
    original = cube.data.copy()
    result = await MeanStack()(cube)
    assert result.meta["foo"] == "bar"
    np.testing.assert_array_equal(cube.data, original)
    assert cube.header["CTYPE3"] == "FRAME"


@pytest.mark.asyncio
@pytest.mark.parametrize("chunk_bytes", [1, 5 * 6 * 4, 5 * 6 * 4 * 3])
async def test_chunking_gives_same_result(chunk_bytes: int) -> None:
    data = random_cube(count=5, ny=7, nx=6)
    full = await MeanStack(uncertainty=True, mask=True)(make_cube(data))
    chunked = await MeanStack(uncertainty=True, mask=True, chunk_bytes=chunk_bytes)(make_cube(data))
    np.testing.assert_array_equal(chunked.data, full.data)
    np.testing.assert_array_equal(chunked.uncertainty, full.uncertainty)
    np.testing.assert_array_equal(chunked.mask, full.mask)


@pytest.mark.asyncio
async def test_all_nan_pixel_is_nan_and_masked() -> None:
    data = np.ones((3, 2, 2), dtype=np.float32)
    data[:, 0, 1] = np.nan
    result = await ZeroSumStack(mask=True)(make_cube(data))
    assert np.isnan(result.data[0, 1])
    assert result.data[0, 0] == 3.0
    assert result.mask[0, 1]
    assert not result.mask[0, 0]


@pytest.mark.asyncio
async def test_no_uncertainty_or_mask_by_default() -> None:
    result = await MeanStack()(make_cube(random_cube()))
    assert result.safe_uncertainty is None
    assert result.safe_mask is None


@pytest.mark.asyncio
async def test_uncertainty_nan_below_two_values() -> None:
    data = np.ones((3, 1, 2), dtype=np.float32)
    data[1:, 0, 1] = np.nan
    result = await ZeroSumStack(uncertainty=True)(make_cube(data))
    assert np.isnan(result.uncertainty[0, 1])
    assert result.uncertainty[0, 0] == 0.0


@pytest.mark.asyncio
async def test_single_frame_stack() -> None:
    data = random_cube(count=1)
    result = await MeanStack(uncertainty=True)(make_cube(data))
    np.testing.assert_array_equal(result.data, data[0].astype(np.float32))
    assert np.all(np.isnan(result.uncertainty))


@pytest.mark.asyncio
async def test_round_trip_through_fits() -> None:
    result = await MeanStack(uncertainty=True, mask=True)(make_cube(random_cube()))
    loaded = Image.from_bytes(result.to_bytes())
    np.testing.assert_allclose(loaded.data, result.data)
    np.testing.assert_allclose(loaded.uncertainty, result.uncertainty)
    np.testing.assert_array_equal(loaded.mask.astype(bool), result.mask)
    assert loaded.header["COMBMETH"] == "mean"
    assert len(loaded.frames) == 5


def test_invalid_chunk_bytes() -> None:
    with pytest.raises(ValueError):
        MeanStack(chunk_bytes=0)


def test_base_class_is_abstract() -> None:
    with pytest.raises(TypeError):
        CombineStack()  # type: ignore[abstract]
