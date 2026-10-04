from __future__ import annotations

import numpy as np
import pytest

from pyobs.utils.stretch import StretchParams, compute_cuts, downsample, stretch_to_uint8


def test_default_stretch_uses_minmax_for_16bit() -> None:
    data = np.array([[1000, 2000], [3000, 4000]], dtype=np.uint16)

    out = stretch_to_uint8(data)

    assert out.dtype == np.uint8
    assert out.min() == 0 and out.max() == 255


def test_full_cuts_roughly_match_old_divide_by_256() -> None:
    data = np.array([[0, 256 * 100], [256 * 200, 65535]], dtype=np.uint16)

    out = stretch_to_uint8(data, StretchParams(cuts="full"))

    # scales by 255/65535 instead of 1/256, so values may differ by one
    assert np.abs(out.astype(int) - np.array([[0, 100], [200, 255]])).max() <= 1


def test_8bit_default_is_unchanged() -> None:
    data = np.array([[10, 20], [30, 40]], dtype=np.uint8)
    assert stretch_to_uint8(data) is data


def test_percentile_and_manual_cuts() -> None:
    data = np.arange(1000, dtype=np.float32).reshape(10, 100)

    lo, hi = compute_cuts(data, StretchParams(cuts="percentile", lo=10, hi=90))
    assert lo == pytest.approx(99.9) and hi == pytest.approx(899.1)
    assert compute_cuts(data, StretchParams(cuts="manual", lo=5, hi=50)) == (5.0, 50.0)


@pytest.mark.parametrize("stretch", ["sqrt", "asinh", "log"])
def test_nonlinear_stretches_brighten_faint_values(stretch: str) -> None:
    data = np.array([[0, 100], [500, 1000]], dtype=np.float32)

    linear = stretch_to_uint8(data, StretchParams(cuts="minmax"))
    other = stretch_to_uint8(data, StretchParams(stretch=stretch, cuts="minmax"))  # type: ignore[arg-type]

    assert other[0, 1] > linear[0, 1]
    assert other[0, 0] == 0 and other[1, 1] == 255


def test_constant_image_does_not_divide_by_zero() -> None:
    out = stretch_to_uint8(np.full((4, 4), 7, dtype=np.uint16))
    assert out.dtype == np.uint8


def test_downsample_block_mean() -> None:
    data = np.arange(16, dtype=np.uint16).reshape(4, 4)
    np.testing.assert_array_equal(downsample(data, 2), [[2.5, 4.5], [10.5, 12.5]])
    assert downsample(data, 1) is data
    with pytest.raises(ValueError):
        downsample(data, 8)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"stretch": "nope"},
        {"cuts": "nope"},
        {"cuts": "manual", "lo": 1.0},
        {"cuts": "percentile", "lo": 90, "hi": 10},
        {"scale": 0},
    ],
)
def test_invalid_params(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        StretchParams(**kwargs)


@pytest.mark.parametrize("cuts", [None, "full"])
def test_downsampled_8bit_keeps_full_range_cuts(cuts: str | None) -> None:
    data = np.full((8, 8), 100, dtype=np.uint8)

    out = stretch_to_uint8(data, StretchParams(cuts=cuts, scale=2))  # type: ignore[arg-type]

    assert out.shape == (4, 4)
    assert np.all(out == 100)


def test_downsampled_16bit_full_cuts_use_input_dtype() -> None:
    data = np.full((8, 8), 32768, dtype=np.uint16)

    out = stretch_to_uint8(data, StretchParams(cuts="full", scale=2))

    assert np.all(out == 128)


def test_dtype_argument_for_already_downsampled_data() -> None:
    binned = np.full((4, 4), 32768.0, dtype=np.float32)

    out = stretch_to_uint8(binned, StretchParams(cuts="full"), dtype=np.uint16)

    assert np.all(out == 128)
    with pytest.raises(ValueError):
        stretch_to_uint8(binned, StretchParams(cuts="full"))
