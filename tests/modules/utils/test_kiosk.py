from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IRunning
from pyobs.interfaces.IWindow import WindowCapabilities
from pyobs.modules import Module
from pyobs.modules.utils.kiosk import Kiosk
from tests.helpers import make_proxy_cm


def make_kiosk(**kwargs: object) -> Kiosk:
    comm = MagicMock(spec=Comm)
    return Kiosk(camera="camera", comm=comm, **kwargs)


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    kiosk = make_kiosk()
    assert kiosk._camera == "camera"
    assert kiosk._port == 37077
    assert kiosk._exp_time == 2.0
    assert kiosk._running is False
    assert kiosk._image is None
    assert kiosk._is_listening is False


def test_init_creates_placeholder_image() -> None:
    kiosk = make_kiosk()
    assert isinstance(kiosk._empty, bytes)
    assert len(kiosk._empty) > 0


def test_init_custom_port() -> None:
    kiosk = make_kiosk(port=12345)
    assert kiosk._port == 12345


# ── image_handler ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_image_handler_returns_placeholder_when_no_image() -> None:
    kiosk = make_kiosk()
    response = await kiosk.image_handler(MagicMock())
    assert response.body == kiosk._empty


@pytest.mark.asyncio
async def test_image_handler_returns_captured_image() -> None:
    kiosk = make_kiosk()
    kiosk._image = b"jpeg-bytes"
    response = await kiosk.image_handler(MagicMock())
    assert response.body == b"jpeg-bytes"


# ── opened ────────────────────────────────────────────────────────────────────


def test_opened_reflects_is_listening() -> None:
    kiosk = make_kiosk()
    assert kiosk.opened is False
    kiosk._is_listening = True
    assert kiosk.opened is True


# ── open/close ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_starts_server_and_publishes_state(mocker) -> None:
    kiosk = make_kiosk()
    mocker.patch.object(Module, "open", AsyncMock())
    kiosk._runner = MagicMock()
    kiosk._runner.setup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock()
    mocker.patch("pyobs.modules.utils.kiosk.web.TCPSite", return_value=site)
    kiosk._comm.set_state = AsyncMock()

    await kiosk.open()

    kiosk._runner.setup.assert_awaited_once()
    site.start.assert_awaited_once()
    assert kiosk._is_listening is True
    kiosk._comm.set_state.assert_awaited_once_with(IRunning, mocker.ANY)
    state = kiosk._comm.set_state.await_args[0][1]
    assert state.running is False


@pytest.mark.asyncio
async def test_close_cleans_up_runner(mocker) -> None:
    kiosk = make_kiosk()
    mocker.patch.object(Module, "close", AsyncMock())
    kiosk._runner = MagicMock()
    kiosk._runner.cleanup = AsyncMock()

    await kiosk.close()

    kiosk._runner.cleanup.assert_awaited_once()


# ── start/stop/is_running ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_sets_running_and_publishes_state() -> None:
    kiosk = make_kiosk()
    kiosk._comm.set_state = AsyncMock()

    await kiosk.start()

    assert kiosk._running is True
    kiosk._comm.set_state.assert_awaited_once()
    interface, state = kiosk._comm.set_state.await_args[0]
    assert interface is IRunning
    assert state.running is True


@pytest.mark.asyncio
async def test_stop_clears_running_and_publishes_state() -> None:
    kiosk = make_kiosk()
    kiosk._running = True
    kiosk._comm.set_state = AsyncMock()

    await kiosk.stop()

    assert kiosk._running is False
    interface, state = kiosk._comm.set_state.await_args[0]
    assert interface is IRunning
    assert state.running is False


@pytest.mark.asyncio
async def test_is_running_reflects_state() -> None:
    kiosk = make_kiosk()
    assert await kiosk.is_running() is False
    kiosk._running = True
    assert await kiosk.is_running() is True


# ── _camera_thread ─────────────────────────────────────────────────────────────


def _cancel_after(n: int):
    """Side effect that raises CancelledError starting from the n-th call."""
    calls = 0

    async def side_effect(*args: object, **kwargs: object) -> bool:
        nonlocal calls
        calls += 1
        if calls > n:
            raise asyncio.CancelledError()
        return True

    return side_effect


@pytest.mark.asyncio
async def test_camera_thread_sleeps_when_not_running(mocker) -> None:
    kiosk = make_kiosk()
    assert kiosk._running is False

    sleep_calls = []

    async def fake_sleep(t: float) -> None:
        sleep_calls.append(t)
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.utils.kiosk.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    assert sleep_calls == [1]


@pytest.mark.asyncio
async def test_camera_thread_sleeps_when_no_camera_proxy(mocker) -> None:
    kiosk = make_kiosk()
    kiosk._running = True
    kiosk._comm.has_proxy = AsyncMock(return_value=False)

    sleep_calls = []

    async def fake_sleep(t: float) -> None:
        sleep_calls.append(t)
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.utils.kiosk.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    assert sleep_calls == [10]


def _make_image(max_value: float = 40000.0) -> MagicMock:
    image = MagicMock()
    image.data = np.array([[max_value]])
    image.to_jpeg = MagicMock(return_value=b"jpeg-bytes")
    return image


@pytest.mark.asyncio
async def test_camera_thread_captures_and_adjusts_exposure_time() -> None:
    kiosk = make_kiosk()
    kiosk._running = True
    kiosk._exp_time = 2.0

    camera = MagicMock()
    camera.set_exposure_time = AsyncMock()
    camera.get_capabilities = MagicMock(
        return_value=WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=100, full_frame_height=100)
    )
    camera.set_window = AsyncMock()
    camera.grab_data = AsyncMock(return_value="image.fits")

    kiosk._comm.has_proxy = AsyncMock(side_effect=_cancel_after(1))
    kiosk._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))
    kiosk._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    image = _make_image(max_value=1000.0)
    kiosk._vfs = MagicMock()
    kiosk._vfs.read_image = AsyncMock(return_value=image)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    camera.set_exposure_time.assert_awaited_once_with(2.0)
    camera.set_window.assert_awaited_once_with(0, 0, 100, 100)
    camera.grab_data.assert_awaited_once_with(False)
    kiosk._vfs.read_image.assert_awaited_once_with("image.fits")
    assert kiosk._image == b"jpeg-bytes"
    # new exptime = old_exptime / max_value * 40000 = 2.0 / 1000 * 40000 = 80.0
    assert kiosk._exp_time == pytest.approx(80.0)


@pytest.mark.asyncio
async def test_camera_thread_clips_exposure_time_to_minimum() -> None:
    kiosk = make_kiosk()
    kiosk._running = True
    kiosk._exp_time = 2.0

    camera = MagicMock()
    camera.set_exposure_time = AsyncMock()
    camera.get_capabilities = MagicMock(return_value=None)
    camera.grab_data = AsyncMock(return_value="image.fits")

    kiosk._comm.has_proxy = AsyncMock(side_effect=_cancel_after(1))
    kiosk._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))
    kiosk._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    # a very bright image drives the computed exptime far below 30
    image = _make_image(max_value=1.0e9)
    kiosk._vfs = MagicMock()
    kiosk._vfs.read_image = AsyncMock(return_value=image)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    camera.set_window.assert_not_called()
    assert kiosk._exp_time == 30


@pytest.mark.asyncio
async def test_camera_thread_continues_on_file_not_found() -> None:
    kiosk = make_kiosk()
    kiosk._running = True

    camera = MagicMock()
    camera.set_exposure_time = AsyncMock()
    camera.get_capabilities = MagicMock(return_value=None)
    camera.grab_data = AsyncMock(return_value="missing.fits")

    kiosk._comm.has_proxy = AsyncMock(side_effect=_cancel_after(1))
    kiosk._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(camera))
    kiosk._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    kiosk._vfs = MagicMock()
    kiosk._vfs.read_image = AsyncMock(side_effect=FileNotFoundError)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    assert kiosk._image is None


@pytest.mark.asyncio
async def test_camera_thread_skips_settings_without_capable_proxies() -> None:
    kiosk = make_kiosk()
    kiosk._running = True

    camera = MagicMock()
    camera.grab_data = AsyncMock(return_value="image.fits")

    kiosk._comm.has_proxy = AsyncMock(side_effect=_cancel_after(1))
    # no exposure-time/window support: safe_proxy yields None
    kiosk._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))
    kiosk._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    image = _make_image(max_value=40000.0)
    kiosk._vfs = MagicMock()
    kiosk._vfs.read_image = AsyncMock(return_value=image)

    with pytest.raises(asyncio.CancelledError):
        await kiosk._camera_thread()

    kiosk._vfs.read_image.assert_awaited_once_with("image.fits")
    assert kiosk._image == b"jpeg-bytes"
