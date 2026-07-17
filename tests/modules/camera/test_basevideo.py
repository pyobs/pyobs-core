from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from pyobs.comm import Comm
from pyobs.events import NewImageEvent
from pyobs.interfaces import IImageType, IVideo
from pyobs.modules import Module
from pyobs.modules.camera.basevideo import BaseVideo, ImageRequest, LastImage, NextImage
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ImageType


def make_basevideo(**kwargs) -> BaseVideo:
    comm = MagicMock(spec=Comm)
    return BaseVideo(comm=comm, **kwargs)


def make_request(filename: str | None = None) -> MagicMock:
    request = MagicMock()
    request.match_info = {} if filename is None else {"filename": filename}
    return request


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    bv = make_basevideo()
    assert bv._port == 37077
    assert bv._interval == 0.5
    assert bv._video_path == "/webcam/video.mjpg"
    assert bv._frame_num == 0
    assert bv._live_view is True
    assert bv._image_type == ImageType.OBJECT
    assert bv._active is False
    assert bv._flip is False
    assert bv._sleep_time == 600
    assert bv._is_listening is False
    assert bv.opened is False


def test_init_custom_values() -> None:
    bv = make_basevideo(http_port=8000, interval=1.5, live_view=False, flip=True, sleep_time=30)
    assert bv._port == 8000
    assert bv._interval == 1.5
    assert bv._live_view is False
    assert bv._flip is True
    assert bv._sleep_time == 30


# ── open / close ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_starts_server_and_publishes_capabilities_and_state(mocker) -> None:
    bv = make_basevideo()
    mocker.patch.object(Module, "open", AsyncMock())
    bv._runner = MagicMock()
    bv._runner.setup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock()
    mocker.patch("pyobs.modules.camera.basevideo.web.TCPSite", return_value=site)
    bv._comm.set_capabilities = AsyncMock()
    bv._comm.set_state = AsyncMock()

    await bv.open()

    assert bv.opened is True
    site.start.assert_awaited_once()

    bv._comm.set_capabilities.assert_awaited_once()
    interface, caps = bv._comm.set_capabilities.await_args[0]
    assert interface is IVideo
    assert caps.video == bv._video_path

    bv._comm.set_state.assert_awaited_once()
    state_interface, state = bv._comm.set_state.await_args[0]
    assert state_interface is IImageType
    assert state.image_type == ImageType.OBJECT


@pytest.mark.asyncio
async def test_close_cleans_up_runner(mocker) -> None:
    bv = make_basevideo()
    mocker.patch.object(Module, "close", AsyncMock())
    bv._runner = MagicMock()
    bv._runner.cleanup = AsyncMock()

    await bv.close()

    bv._runner.cleanup.assert_awaited_once()


# ── web_handler / ping_handler ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_web_handler_returns_html() -> None:
    bv = make_basevideo()
    response = await bv.web_handler(make_request())
    assert response.content_type == "text/html"
    assert response.status == 200


@pytest.mark.asyncio
async def test_ping_handler_returns_ok_status() -> None:
    bv = make_basevideo()
    response = await bv.ping_handler(make_request())
    assert response.status == 200
    assert response.content_type == "application/json"


# ── image_handler ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_image_handler_returns_cached_data() -> None:
    bv = make_basevideo()
    bv._cache["test.fits"] = b"fits-bytes"

    response = await bv.image_handler(make_request("test.fits"))

    assert response.body == b"fits-bytes"
    assert response.content_type == "image/fits"


@pytest.mark.asyncio
async def test_image_handler_404_when_missing() -> None:
    from aiohttp import web

    bv = make_basevideo()
    with pytest.raises(web.HTTPNotFound):
        await bv.image_handler(make_request("missing.fits"))


# ── camera_active / activate_camera / deactivate_camera ────────────────────


@pytest.mark.asyncio
async def test_activate_camera_from_inactive_calls_hook() -> None:
    bv = make_basevideo()
    bv._activate_camera = AsyncMock()

    await bv.activate_camera()

    assert bv.camera_active is True
    bv._activate_camera.assert_awaited_once()
    assert bv._active_time > 0


@pytest.mark.asyncio
async def test_activate_camera_when_already_active_skips_hook() -> None:
    bv = make_basevideo()
    bv._active = True
    bv._activate_camera = AsyncMock()

    await bv.activate_camera()

    bv._activate_camera.assert_not_called()


@pytest.mark.asyncio
async def test_deactivate_camera_from_active_calls_hook() -> None:
    bv = make_basevideo()
    bv._active = True
    bv._deactivate_camera = AsyncMock()

    await bv.deactivate_camera()

    assert bv.camera_active is False
    bv._deactivate_camera.assert_awaited_once()
    assert bv._active_time == 0


@pytest.mark.asyncio
async def test_deactivate_camera_when_already_inactive_skips_hook() -> None:
    bv = make_basevideo()
    bv._deactivate_camera = AsyncMock()

    await bv.deactivate_camera()

    bv._deactivate_camera.assert_not_called()


# ── _active_update ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_active_update_deactivates_after_sleep_timeout(mocker) -> None:
    bv = make_basevideo(sleep_time=10)
    bv._active = True
    bv.deactivate_camera = AsyncMock()
    # first call resets _active_time (at method entry); second is the in-loop check, 900s later
    mocker.patch("pyobs.modules.camera.basevideo.time.time", side_effect=[100.0, 1000.0])

    async def fake_sleep(t: float) -> None:
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.camera.basevideo.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await bv._active_update()

    bv.deactivate_camera.assert_awaited_once()


@pytest.mark.asyncio
async def test_active_update_skips_deactivate_when_recently_active(mocker) -> None:
    bv = make_basevideo(sleep_time=600)
    bv._active = True
    bv.deactivate_camera = AsyncMock()

    async def fake_sleep(t: float) -> None:
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.camera.basevideo.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await bv._active_update()

    bv.deactivate_camera.assert_not_called()


# ── image_jpeg ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_image_jpeg_returns_none_when_no_last_image() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()

    num, jpeg = await bv.image_jpeg()

    bv.activate_camera.assert_awaited_once()
    assert num == 0
    assert jpeg is None


@pytest.mark.asyncio
async def test_image_jpeg_returns_last_jpeg() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()
    bv._frame_num = 5
    bv._last_image = LastImage(data=np.zeros((2, 2)), image=None, jpeg=b"jpeg-bytes", filename=None)

    num, jpeg = await bv.image_jpeg()

    assert num == 5
    assert jpeg == b"jpeg-bytes"


# ── create_jpeg ─────────────────────────────────────────────────────────────


def test_create_jpeg_converts_uint16() -> None:
    data = np.full((4, 4), 40000, dtype=np.uint16)
    jpeg = BaseVideo.create_jpeg(data)
    assert jpeg.startswith(b"\xff\xd8")  # JPEG magic bytes


def test_create_jpeg_handles_uint8() -> None:
    data = np.full((4, 4), 200, dtype=np.uint8)
    jpeg = BaseVideo.create_jpeg(data)
    assert jpeg.startswith(b"\xff\xd8")


# ── _set_image ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_image_stores_last_image_and_increments_frame_num() -> None:
    bv = make_basevideo(live_view=False)
    data = np.zeros((4, 4))

    await bv._set_image(data)

    assert bv._frame_num == 1
    assert bv._last_image is not None
    assert bv._last_image.data is data
    assert bv._last_image.jpeg is None  # live_view disabled


@pytest.mark.asyncio
async def test_set_image_flips_when_configured() -> None:
    bv = make_basevideo(live_view=False, flip=True)
    data = np.arange(16).reshape(4, 4).astype(float)

    await bv._set_image(data)

    np.testing.assert_array_equal(bv._last_image.data, np.flip(data, axis=0))


@pytest.mark.asyncio
async def test_set_image_generates_jpeg_when_live_view_enabled() -> None:
    bv = make_basevideo(live_view=True, interval=0.0)
    data = np.zeros((4, 4), dtype=np.uint8)

    await bv._set_image(data)

    assert bv._last_image.jpeg is not None
    assert bv._last_image.jpeg.startswith(b"\xff\xd8")


@pytest.mark.asyncio
async def test_set_image_throttles_jpeg_generation_by_interval() -> None:
    bv = make_basevideo(live_view=True, interval=1000.0)
    bv._last_time = __import__("time").time()  # just generated one

    await bv._set_image(np.zeros((4, 4)))

    assert bv._last_image.jpeg is None  # interval not elapsed yet


@pytest.mark.asyncio
async def test_set_image_creates_image_and_fulfills_pending_requests() -> None:
    bv = make_basevideo(live_view=False)
    bv.request_fits_headers = AsyncMock(return_value={})
    bv._create_image = AsyncMock(return_value=("the-image", "the-filename.fits"))

    request = ImageRequest(broadcast=True)
    bv._image_requests.append(request)
    bv._next_image = NextImage(date_obs="now", image_type=ImageType.OBJECT, header_futures={}, broadcast=True)

    await bv._set_image(np.zeros((4, 4)))

    assert request.image == "the-image"
    assert request.filename == "the-filename.fits"
    # request is still pending (not yet removed by grab_data()), so a fresh
    # _next_image gets prepared again for the following frame
    assert bv._next_image is not None


@pytest.mark.asyncio
async def test_set_image_prepares_next_image_when_requests_pending() -> None:
    bv = make_basevideo(live_view=False)
    bv.request_fits_headers = AsyncMock(return_value={"h": "x"})
    bv._image_requests.append(ImageRequest(broadcast=True))

    await bv._set_image(np.zeros((4, 4)))

    assert bv._next_image is not None
    assert bv._next_image.image_type == bv._image_type
    assert bv._next_image.broadcast is True
    assert bv._next_image.header_futures == {"h": "x"}


@pytest.mark.asyncio
async def test_set_image_does_not_prepare_next_image_without_requests() -> None:
    bv = make_basevideo(live_view=False)
    bv.request_fits_headers = AsyncMock(return_value={})

    await bv._set_image(np.zeros((4, 4)))

    assert bv._next_image is None


# ── _create_image ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_image_sets_headers_and_delegates_to_finish() -> None:
    bv = make_basevideo()
    bv.add_requested_fits_headers = AsyncMock()
    bv.add_fits_headers = AsyncMock()
    bv._finish_image = AsyncMock(return_value=("image", "filename.fits"))
    next_image = NextImage(
        date_obs="2024-01-01T00:00:00", image_type=ImageType.DARK, header_futures={}, broadcast=False
    )

    result = await bv._create_image(np.zeros((4, 4)), next_image)

    assert result == ("image", "filename.fits")
    bv.add_requested_fits_headers.assert_awaited_once()
    bv.add_fits_headers.assert_awaited_once()
    image_arg = bv.add_requested_fits_headers.await_args[0][0]
    assert image_arg.header["DATE-OBS"] == "2024-01-01T00:00:00"
    assert image_arg.header["IMAGETYP"] == ImageType.DARK
    bv._finish_image.assert_awaited_once_with(image_arg, False, ImageType.DARK)


# ── _finish_image ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finish_image_writes_to_cache_and_returns_filename() -> None:
    bv = make_basevideo()
    bv.format_filename = MagicMock(return_value="/webcam/test.fits")
    from pyobs.images import Image

    image = Image(data=np.zeros((4, 4)))
    image.header["FNAME"] = "test.fits"

    result_image, filename = await bv._finish_image(image, broadcast=False, image_type=ImageType.OBJECT)

    assert filename == "/webcam/test.fits"
    assert "test.fits" in bv._cache


@pytest.mark.asyncio
async def test_finish_image_broadcasts_new_image_event() -> None:
    bv = make_basevideo()
    bv.format_filename = MagicMock(return_value="/webcam/test.fits")
    bv._comm.send_event = AsyncMock()
    from pyobs.images import Image

    image = Image(data=np.zeros((4, 4)))
    image.header["FNAME"] = "test.fits"

    await bv._finish_image(image, broadcast=True, image_type=ImageType.OBJECT)

    bv._comm.send_event.assert_awaited_once()
    event = bv._comm.send_event.await_args[0][0]
    assert isinstance(event, NewImageEvent)


@pytest.mark.asyncio
async def test_finish_image_skips_broadcast_when_not_requested() -> None:
    bv = make_basevideo()
    bv.format_filename = MagicMock(return_value="/webcam/test.fits")
    bv._comm.send_event = AsyncMock()
    from pyobs.images import Image

    image = Image(data=np.zeros((4, 4)))
    image.header["FNAME"] = "test.fits"

    await bv._finish_image(image, broadcast=False, image_type=ImageType.OBJECT)

    bv._comm.send_event.assert_not_called()


# ── grab_data ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_data_returns_filename_once_fulfilled() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()

    async def fulfill_after_delay() -> None:
        await asyncio.sleep(0.02)
        async with bv._image_request_lock:
            for req in bv._image_requests:
                req.image = "image"
                req.filename = "grabbed.fits"

    asyncio.create_task(fulfill_after_delay())

    filename = await bv.grab_data(broadcast=True)

    assert filename == "grabbed.fits"
    assert len(bv._image_requests) == 0  # removed after fulfillment


@pytest.mark.asyncio
async def test_grab_data_raises_when_never_gets_filename() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()

    async def fulfill_with_no_filename() -> None:
        await asyncio.sleep(0.02)
        async with bv._image_request_lock:
            for req in bv._image_requests:
                req.image = "image"
                req.filename = None

    asyncio.create_task(fulfill_with_no_filename())

    with pytest.raises(exc.GrabImageError):
        await bv.grab_data()


# ── set_image_type ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_image_type_updates_state_and_type() -> None:
    bv = make_basevideo()
    bv._comm.set_state = AsyncMock()

    await bv.set_image_type(ImageType.DARK)

    assert bv._image_type == ImageType.DARK
    bv._comm.set_state.assert_awaited_once()
    interface, state = bv._comm.set_state.await_args[0]
    assert interface is IImageType
    assert state.image_type == ImageType.DARK
