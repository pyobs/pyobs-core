from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.robotic.scripts.calibration.darkbias import DarkBiasScript
from pyobs.utils.enums import ImageType


def make_script(**kwargs) -> DarkBiasScript:
    s = DarkBiasScript(camera="camera", **kwargs)
    s._comm = MagicMock()
    return s


def make_camera(
    supports_binning=True, supports_window=True, supports_exptime=True, supports_imagetype=True
) -> MagicMock:
    """Create a mock camera supporting all or some interfaces."""
    from pyobs.interfaces import IBinning, ICamera, IData, IExposureTime, IImageType, IWindow

    interfaces = [ICamera, IData]
    if supports_binning:
        interfaces.append(IBinning)
    if supports_window:
        interfaces.append(IWindow)
    if supports_exptime:
        interfaces.append(IExposureTime)
    if supports_imagetype:
        interfaces.append(IImageType)

    camera = MagicMock(spec=interfaces)
    camera.set_binning = AsyncMock()
    camera.get_full_frame = AsyncMock(return_value=(0, 0, 1024, 1024))
    camera.set_window = AsyncMock()
    camera.set_exposure_time = AsyncMock()
    camera.set_image_type = AsyncMock()
    camera.grab_data = AsyncMock()

    # make isinstance checks work
    camera.__class__ = type("Camera", tuple(interfaces), {})
    return camera


def make_proxy_cm(value: object) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def setup_run_comm(script: DarkBiasScript, camera: MagicMock, binning_cam=..., window_cam=...) -> None:
    """Wire up comm mocks for a DarkBiasScript.run call.

    safe_proxy is used for IBinning and IWindow (optional interfaces).
    proxy is used for IExposureTime, IImageType, and IData (required).

    Pass binning_cam=None or window_cam=None to simulate a camera that doesn't
    implement the corresponding interface.
    """
    from pyobs.interfaces import IBinning, IWindow

    binning_value = camera if binning_cam is ... else binning_cam
    window_value = camera if window_cam is ... else window_cam

    def safe_proxy_se(name, iface=None):
        if iface is IBinning:
            return make_proxy_cm(binning_value)
        if iface is IWindow:
            return make_proxy_cm(window_value)
        return make_proxy_cm(camera)

    script._comm.safe_proxy = MagicMock(side_effect=safe_proxy_se)
    script._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_true_when_camera_available() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=True)
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_false_when_camera_unavailable() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=False)
    assert await script.can_run(None) is False


# ── bias vs dark ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runs_bias_when_exptime_zero() -> None:
    script = make_script(count=3, exptime=0)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_image_type.assert_called_once_with(ImageType.BIAS)
    camera.set_exposure_time.assert_called_once_with(0)
    assert camera.grab_data.call_count == 3


@pytest.mark.asyncio
async def test_runs_dark_when_exptime_nonzero() -> None:
    script = make_script(count=2, exptime=30.0)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_image_type.assert_called_once_with(ImageType.DARK)
    camera.set_exposure_time.assert_called_once_with(30.0)
    assert camera.grab_data.call_count == 2


# ── interface checks ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sets_binning_when_supported() -> None:
    script = make_script(binning=(2, 2))
    camera = make_camera(supports_binning=True)
    setup_run_comm(script, camera)

    await script.run(None)
    camera.set_binning.assert_called_once_with(2, 2)


@pytest.mark.asyncio
async def test_skips_binning_when_not_supported() -> None:
    script = make_script(binning=(2, 2))
    camera = make_camera(supports_binning=False)
    setup_run_comm(script, camera, binning_cam=None)

    await script.run(None)
    camera.set_binning.assert_not_called()


@pytest.mark.asyncio
async def test_sets_full_frame_when_window_supported() -> None:
    script = make_script()
    camera = make_camera(supports_window=True)
    setup_run_comm(script, camera)

    await script.run(None)
    camera.get_full_frame.assert_called_once()
    camera.set_window.assert_called_once_with(0, 0, 1024, 1024)


@pytest.mark.asyncio
async def test_skips_window_when_not_supported() -> None:
    script = make_script()
    camera = make_camera(supports_window=False)
    setup_run_comm(script, camera, window_cam=None)

    await script.run(None)
    camera.set_window.assert_not_called()


@pytest.mark.asyncio
async def test_takes_correct_count() -> None:
    script = make_script(count=5)
    camera = make_camera()
    setup_run_comm(script, camera)

    await script.run(None)
    assert camera.grab_data.call_count == 5
