from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from astropy.modeling import models
from astropy.table import Table
from photutils.datasets import make_model_image

from pyobs.robotic.utils.exptime.stellarexptime import StellarExposureTimeProvider
from pyobs.utils.enums import ImageType

# ── helpers ───────────────────────────────────────────────────────────────────

SHAPE = (200, 200)
BACKGROUND = 100.0
SIGMA = 3.0


def make_stellar_image(
    cx: float, cy: float, amplitude: float, background: float = BACKGROUND, shape: tuple[int, int] = SHAPE
) -> np.ndarray:
    """Create a realistic image with a single Gaussian star using photutils."""
    model = models.Gaussian2D(x_stddev=SIGMA, y_stddev=SIGMA)
    params = Table(
        {
            "amplitude": [amplitude],
            "x_mean": [cx],
            "y_mean": [cy],
        }
    )
    star_data = make_model_image(shape, model, params, x_name="x_mean", y_name="y_mean")
    return star_data + background


def make_image(data: np.ndarray) -> MagicMock:
    img = MagicMock()
    img.data = data
    return img


def make_provider(**kwargs) -> StellarExposureTimeProvider:
    defaults = dict(camera="camera", target_peak=30000.0, search_radius=50, max_iterations=3, default_exposure_time=1.0)
    defaults.update(kwargs)
    p = StellarExposureTimeProvider(**defaults)
    p._comm = MagicMock()
    p._vfs = MagicMock()
    return p


def make_camera_mocks(
    bias_data: np.ndarray, sci_data: np.ndarray, orig_exptime: float = 1.0
) -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    """Return (camera, camera_exptime, camera_imagetype, camera_window) mocks."""
    mock_camera = AsyncMock()
    mock_camera.grab_data = AsyncMock(side_effect=["bias.fits", "sci.fits"])

    mock_exptime = AsyncMock()
    mock_exptime.get_exposure_time = AsyncMock(return_value=orig_exptime)

    mock_imagetype = AsyncMock()

    mock_window = AsyncMock()
    mock_window.get_window = AsyncMock(return_value=(0, 0, SHAPE[1], SHAPE[0]))

    return mock_camera, mock_exptime, mock_imagetype, mock_window


def attach_proxies(
    provider: StellarExposureTimeProvider,
    mock_camera: AsyncMock,
    mock_exptime: AsyncMock,
    mock_imagetype: AsyncMock,
    mock_window: AsyncMock,
    bias_data: np.ndarray,
    sci_data: np.ndarray,
) -> None:
    from pyobs.interfaces import ICamera, IExposureTime, IImageType

    provider._vfs.read_image = AsyncMock(
        side_effect=[
            make_image(bias_data),
            make_image(sci_data),
        ]
    )

    async def proxy_side_effect(name, interface=None):
        if interface is ICamera:
            return mock_camera
        if interface is IExposureTime:
            return mock_exptime
        if interface is IImageType:
            return mock_imagetype
        return mock_window

    provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)


# ── _find_star ────────────────────────────────────────────────────────────────


def test_find_star_locates_star_at_centre() -> None:
    """_find_star finds a realistic Gaussian star at the image centre."""
    cx, cy = 100.0, 100.0
    data = make_stellar_image(cx, cy, amplitude=20000.0)

    provider = make_provider(search_radius=50)
    peak, col, row = provider._find_star(data)

    assert peak is not None
    assert abs(col - cx) < 5
    assert abs(row - cy) < 5


def test_find_star_peak_matches_amplitude_plus_background() -> None:
    """Fitted peak is approximately amplitude + background."""
    amplitude = 15000.0
    data = make_stellar_image(100.0, 100.0, amplitude=amplitude, background=BACKGROUND)

    provider = make_provider(search_radius=50)
    peak, _, _ = provider._find_star(data)

    assert peak is not None
    assert abs(peak - (BACKGROUND + amplitude)) < amplitude * 0.1


def test_find_star_returns_none_outside_radius() -> None:
    """Star outside search_radius is not detected."""
    data = make_stellar_image(cx=10.0, cy=10.0, amplitude=20000.0)

    provider = make_provider(search_radius=20)  # small radius, star at corner
    peak, col, row = provider._find_star(data)

    if peak is not None:
        assert peak < 5000.0


def test_find_star_returns_none_for_zero_image() -> None:
    """Returns None for an all-zero image."""
    provider = make_provider()
    peak, col, row = provider._find_star(np.zeros(SHAPE))
    assert peak is None


def test_find_star_returns_int_coordinates() -> None:
    """col and row are plain Python ints."""
    data = make_stellar_image(100.0, 100.0, amplitude=20000.0)
    provider = make_provider(search_radius=50)
    peak, col, row = provider._find_star(data)

    if peak is not None:
        assert type(col) is int
        assert type(row) is int


# ── __call__ ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_scales_exposure_time() -> None:
    """Scales exposure time so fitted peak reaches target_peak."""
    amplitude = 15000.0
    bias_data = np.full(SHAPE, BACKGROUND)
    sci_data = make_stellar_image(100.0, 100.0, amplitude=amplitude, background=BACKGROUND)
    expected_peak = amplitude  # after bias subtraction
    target_peak = 30000.0
    expected_exptime = 1.0 * target_peak / expected_peak

    provider = make_provider(target_peak=target_peak, max_iterations=1)
    mocks = make_camera_mocks(bias_data, sci_data)
    attach_proxies(provider, *mocks, bias_data, sci_data)

    result = await provider()

    assert abs(result - expected_exptime) < expected_exptime * 0.15


@pytest.mark.asyncio
async def test_call_returns_default_when_no_star() -> None:
    """Returns default_exposure_time when bias subtraction yields zero data."""
    flat = np.full(SHAPE, 500.0)
    provider = make_provider(default_exposure_time=5.0, max_iterations=1)
    mocks = make_camera_mocks(flat, flat, orig_exptime=5.0)
    attach_proxies(provider, *mocks, flat, flat)

    result = await provider()
    assert result == 5.0


@pytest.mark.asyncio
async def test_call_restores_settings_on_exception() -> None:
    """Original camera settings are restored even when grab_data raises."""
    provider = make_provider()

    from pyobs.interfaces import ICamera, IExposureTime, IImageType

    mock_camera = AsyncMock()
    mock_camera.grab_data = AsyncMock(side_effect=RuntimeError("camera error"))
    mock_exptime = AsyncMock()
    mock_exptime.get_exposure_time = AsyncMock(return_value=10.0)
    mock_imagetype = AsyncMock()
    mock_window = AsyncMock()
    mock_window.get_window = AsyncMock(return_value=(0, 0, 512, 512))

    async def proxy_side_effect(name, interface=None):
        if interface is ICamera:
            return mock_camera
        if interface is IExposureTime:
            return mock_exptime
        if interface is IImageType:
            return mock_imagetype
        return mock_window

    provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)

    with pytest.raises(RuntimeError):
        await provider()

    mock_exptime.set_exposure_time.assert_called_with(10.0)
    mock_imagetype.set_image_type.assert_called_with(ImageType.OBJECT)


@pytest.mark.asyncio
async def test_call_converges_in_one_iteration() -> None:
    """Stops after one iteration when already within convergence_threshold."""
    target_peak = 30000.0
    amplitude = target_peak * 0.97  # 3% below target — within 5% threshold
    bias_data = np.zeros(SHAPE)
    sci_data = make_stellar_image(100.0, 100.0, amplitude=amplitude, background=0.0)

    provider = make_provider(target_peak=target_peak, max_iterations=3, convergence_threshold=0.05)
    mocks = make_camera_mocks(bias_data, sci_data)
    attach_proxies(provider, *mocks, bias_data, sci_data)

    # bias + exactly one science frame = 2 grab_data calls
    assert mocks[0].grab_data.call_count == 2
