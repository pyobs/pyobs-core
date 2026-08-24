from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from aiohttp import web

from pyobs.comm import Comm
from pyobs.events import NewImageEvent
from pyobs.interfaces import IImageType, IVideo
from pyobs.modules import Module
from pyobs.modules.camera.basevideo import _COOKIE_NAME, BaseVideo, ImageRequest, LastImage, NextImage
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ImageType


def make_basevideo(**kwargs) -> BaseVideo:
    comm = MagicMock(spec=Comm)
    return BaseVideo(comm=comm, **kwargs)


def make_request(
    filename: str | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> MagicMock:
    request = MagicMock()
    request.match_info = {} if filename is None else {"filename": filename}
    request.headers = headers or {}
    request.cookies = cookies or {}
    return request


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    bv = make_basevideo()
    assert bv._port == 37077
    assert bv._interval == 0.5
    assert bv._video_path == "/webcam/video.mjpg"
    assert bv._raw_path == "/webcam/video.raw"
    assert bv._frame_num == 0
    assert bv._image_type == ImageType.OBJECT
    assert bv._active is False
    assert bv._flip is False
    assert bv._sleep_time == 60
    assert bv._is_listening is False
    assert bv.opened is False


def test_init_custom_values() -> None:
    bv = make_basevideo(http_port=8000, interval=1.5, video_path=None, raw_path=None, flip=True, sleep_time=30)
    assert bv._port == 8000
    assert bv._interval == 1.5
    assert bv._video_path is None
    assert bv._raw_path is None
    assert bv._flip is True
    assert bv._sleep_time == 30


def test_fits_header_timeout_reaches_mixin() -> None:
    """BaseVideo must forward fits_header_timeout to ImageFitsHeaderMixin, not swallow it into
    Module's catch-all **kwargs -- see issue #764 / PR #765."""
    bv = make_basevideo(fits_header_timeout=1.0)
    assert bv._fitsheadermixin_header_timeout == 1.0


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
    assert caps.mjpeg == bv._video_path
    assert caps.raw == bv._raw_path

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
    bv._last_image = LastImage(
        data=np.zeros((2, 2)), image=None, jpeg=b"jpeg-bytes", filename=None, date_obs="2024-01-01T00:00:00.000000"
    )

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
    bv = make_basevideo(video_path=None)
    data = np.zeros((4, 4))

    await bv._set_image(data)

    assert bv._frame_num == 1
    assert bv._last_image is not None
    assert bv._last_image.data is data
    assert bv._last_image.jpeg is None  # video_path disabled


@pytest.mark.asyncio
async def test_set_image_flips_when_configured() -> None:
    bv = make_basevideo(video_path=None, flip=True)
    data = np.arange(16).reshape(4, 4).astype(float)

    await bv._set_image(data)

    np.testing.assert_array_equal(bv._last_image.data, np.flip(data, axis=0))


@pytest.mark.asyncio
async def test_set_image_generates_jpeg_when_video_enabled() -> None:
    bv = make_basevideo(interval=0.0)
    data = np.zeros((4, 4), dtype=np.uint8)

    await bv._set_image(data)

    assert bv._last_image.jpeg is not None
    assert bv._last_image.jpeg.startswith(b"\xff\xd8")


@pytest.mark.asyncio
async def test_set_image_throttles_jpeg_generation_by_interval() -> None:
    bv = make_basevideo(interval=1000.0)
    bv._last_time = __import__("time").time()  # just generated one

    await bv._set_image(np.zeros((4, 4)))

    assert bv._last_image.jpeg is None  # interval not elapsed yet


@pytest.mark.asyncio
async def test_set_image_creates_image_and_fulfills_pending_requests() -> None:
    bv = make_basevideo(video_path=None)
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
    bv = make_basevideo(video_path=None)
    bv.request_fits_headers = AsyncMock(return_value={"h": "x"})
    bv._image_requests.append(ImageRequest(broadcast=True))

    await bv._set_image(np.zeros((4, 4)))

    assert bv._next_image is not None
    assert bv._next_image.image_type == bv._image_type
    assert bv._next_image.broadcast is True
    assert bv._next_image.header_futures == {"h": "x"}


@pytest.mark.asyncio
async def test_set_image_does_not_prepare_next_image_without_requests() -> None:
    bv = make_basevideo(video_path=None)
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


# ── route registration gating ───────────────────────────────────────────────


def _route_paths(bv: BaseVideo) -> set[str]:
    return {r.resource.canonical for r in bv._app.router.routes()}


def test_routes_registered_by_default() -> None:
    bv = make_basevideo()
    paths = _route_paths(bv)
    assert "/" in paths
    assert "/video.mjpg" in paths
    assert "/video.raw" in paths
    assert "/ping" in paths
    assert "/{filename}" in paths


def test_routes_not_registered_when_video_disabled() -> None:
    bv = make_basevideo(video_path=None)
    paths = _route_paths(bv)
    assert "/" not in paths
    assert "/video.mjpg" not in paths
    assert "/video.raw" in paths
    assert "/ping" in paths
    assert "/{filename}" in paths


def test_routes_not_registered_when_raw_disabled() -> None:
    bv = make_basevideo(raw_path=None)
    paths = _route_paths(bv)
    assert "/" in paths
    assert "/video.mjpg" in paths
    assert "/video.raw" not in paths
    assert "/ping" in paths
    assert "/{filename}" in paths


# ── raw-frame streaming ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_image_sets_new_frame_event() -> None:
    bv = make_basevideo(video_path=None)
    bv._new_frame.clear()

    await bv._set_image(np.zeros((4, 4)))

    assert bv._new_frame.is_set()


@pytest.mark.asyncio
async def test_new_frame_event_coalesces_multiple_sets() -> None:
    bv = make_basevideo(video_path=None)
    bv._new_frame.clear()

    for _ in range(5):
        await bv._set_image(np.zeros((4, 4)))

    # asyncio.Event is a boolean, not a counter: five sets collapse into one wake
    assert bv._new_frame.is_set()
    bv._new_frame.clear()
    assert not bv._new_frame.is_set()


def test_raw_frame_meta_and_little_endian_bytes() -> None:
    bv = make_basevideo()
    data = np.arange(6, dtype=np.uint16).reshape(2, 3)

    meta_bytes, frame = bv._raw_frame(data, "2024-01-01T00:00:00.000000")

    meta = json.loads(meta_bytes)
    assert meta["DTYPE"] == "<u2"
    assert meta["NAXIS1"] == 3
    assert meta["NAXIS2"] == 2
    assert "DATE-OBS" in meta
    assert "IMAGETYP" in meta
    # little-endian: value 0 -> 00 00, value 1 -> 01 00
    assert frame == data.astype("<u2").tobytes()
    assert frame[:4] == b"\x00\x00\x01\x00"


@pytest.mark.asyncio
async def test_raw_handler_writes_once_per_wake_and_keeps_active(mocker) -> None:
    bv = make_basevideo()

    # several frames arriving before the handler starts coalesce into a single wake
    for _ in range(3):
        await bv._set_image(np.zeros((4, 4), dtype=np.uint16))

    response = MagicMock()
    response.prepare = AsyncMock()
    from aiohttp.client_exceptions import ClientConnectionResetError

    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)

    await bv.raw_handler(make_request())

    # one wake -> one write, despite three _set_image calls; connection is active
    assert response.write.await_count == 1
    assert bv.camera_active is True
    assert bv._active_time > 0


@pytest.mark.asyncio
async def test_raw_handler_touches_activity_without_new_frame(mocker) -> None:
    # no frame has arrived yet -- the wait must time out and re-touch activity
    # anyway, per design doc §5, instead of blocking indefinitely
    bv = make_basevideo(sleep_time=0.02)

    response = MagicMock()
    response.prepare = AsyncMock()
    from aiohttp.client_exceptions import ClientConnectionResetError

    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)

    real_activate = bv.activate_camera
    activate_calls = 0

    async def activate_side_effect() -> None:
        nonlocal activate_calls
        activate_calls += 1
        await real_activate()
        if activate_calls == 2:
            # this is the timeout-triggered re-touch with no frame yet produced;
            # now produce one so the next loop iteration can wake normally
            await bv._set_image(np.zeros((2, 2), dtype=np.uint16))

    bv.activate_camera = activate_side_effect  # type: ignore[method-assign]

    await bv.raw_handler(make_request())

    # call #1: on connect: call #2: timeout re-touch (no frame yet); call #3: after real wake
    assert activate_calls >= 2
    assert response.write.await_count == 1
    assert bv.camera_active is True


@pytest.mark.asyncio
async def test_raw_handler_dedupes_frame_build_across_consumers(mocker) -> None:
    # two simultaneous raw clients waking for the *same* frame must not each pay for
    # the header build/JSON serialization/tobytes() copy -- only the first computes
    # it, the second reuses the cached (meta, frame) bytes (#769). Both handlers are
    # started while genuinely blocked on the (unset) event, so a single set() wakes
    # both in the same batch -- mirrors Event.wait()'s real coalescing behavior,
    # unlike calling raw_handler() while the event happens to already be set.
    bv = make_basevideo()
    await bv._set_image(np.zeros((4, 4), dtype=np.uint16))
    bv._new_frame.clear()

    from aiohttp.client_exceptions import ClientConnectionResetError

    responses = []

    def make_response(*args, **kwargs) -> MagicMock:
        response = MagicMock()
        response.prepare = AsyncMock()
        response.write = AsyncMock(side_effect=ClientConnectionResetError())
        responses.append(response)
        return response

    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", side_effect=make_response)
    raw_frame_spy = mocker.spy(bv, "_raw_frame")

    task1 = asyncio.create_task(bv.raw_handler(make_request()))
    task2 = asyncio.create_task(bv.raw_handler(make_request()))
    await asyncio.sleep(0)  # let both tasks reach the event wait and actually suspend

    await bv._set_image(np.ones((4, 4), dtype=np.uint16))  # single wake -> both proceed

    await asyncio.wait_for(asyncio.gather(task1, task2), timeout=2)

    assert raw_frame_spy.call_count == 1
    assert len(responses) == 2
    assert responses[0].write.await_args.args == responses[1].write.await_args.args


@pytest.mark.asyncio
async def test_raw_handler_recomputes_after_new_frame(mocker) -> None:
    # the cache must not serve stale bytes once a new frame has arrived
    bv = make_basevideo()
    await bv._set_image(np.zeros((4, 4), dtype=np.uint16))

    from aiohttp.client_exceptions import ClientConnectionResetError

    response = MagicMock()
    response.prepare = AsyncMock()
    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)
    raw_frame_spy = mocker.spy(bv, "_raw_frame")

    await bv.raw_handler(make_request())
    await bv._set_image(np.ones((4, 4), dtype=np.uint16))
    await bv.raw_handler(make_request())

    assert raw_frame_spy.call_count == 2


# ── token auth ─────────────────────────────────────────────────────────────


def _session_value(token: str, expiry: int | None = None) -> str:
    """Build a valid session-cookie value for the given token (mirror of BaseVideo._make_session_value)."""
    expiry = int(time.time()) + 24 * 60 * 60 if expiry is None else expiry
    signature = hmac.new(token.encode(), str(expiry).encode(), hashlib.sha256).hexdigest()
    return f"{expiry}.{signature}"


# route registration gating


def test_token_param_stored() -> None:
    bv = make_basevideo(token="secret")
    assert bv._token == "secret"


def test_login_routes_not_registered_without_token() -> None:
    bv = make_basevideo()
    paths = _route_paths(bv)
    assert "/login" not in paths
    assert "/logout" not in paths


def test_login_routes_registered_with_token() -> None:
    bv = make_basevideo(token="secret")
    paths = _route_paths(bv)
    assert "/login" in paths
    assert "/logout" in paths


# _check_auth


def test_check_auth_noop_without_token() -> None:
    bv = make_basevideo()
    bv._check_auth(make_request())  # must not raise


def test_check_auth_raises_without_credentials() -> None:
    bv = make_basevideo(token="secret")
    with pytest.raises(web.HTTPUnauthorized):
        bv._check_auth(make_request())


def test_check_auth_accepts_bearer_and_cookie() -> None:
    bv = make_basevideo(token="secret")
    bv._check_auth(make_request(headers={"Authorization": "Bearer secret"}))  # must not raise
    bv._check_auth(make_request(cookies={_COOKIE_NAME: _session_value("secret")}))  # must not raise


def test_make_session_value_roundtrips_through_check_cookie() -> None:
    bv = make_basevideo(token="secret")
    assert bv._check_cookie(make_request(cookies={_COOKIE_NAME: bv._make_session_value()})) is True


# web_handler: unauthenticated browser gets a redirect to the login page, not a bare 401


@pytest.mark.asyncio
async def test_web_handler_redirects_to_login_when_unauthenticated() -> None:
    bv = make_basevideo(token="secret")
    with pytest.raises(web.HTTPSeeOther) as exc:
        await bv.web_handler(make_request())
    assert exc.value.location == "/login"


@pytest.mark.asyncio
async def test_web_handler_accepts_valid_bearer() -> None:
    bv = make_basevideo(token="secret")
    response = await bv.web_handler(make_request(headers={"Authorization": "Bearer secret"}))
    assert response.status == 200
    assert response.content_type == "text/html"


@pytest.mark.asyncio
async def test_web_handler_accepts_valid_cookie() -> None:
    bv = make_basevideo(token="secret")
    response = await bv.web_handler(make_request(cookies={_COOKIE_NAME: _session_value("secret")}))
    assert response.status == 200


# streaming handlers: 401 raised before StreamResponse.prepare() is reached


@pytest.mark.asyncio
async def test_video_handler_401_without_auth_before_prepare(mocker) -> None:
    bv = make_basevideo(token="secret")
    response = MagicMock()
    response.prepare = AsyncMock()
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)

    with pytest.raises(web.HTTPUnauthorized):
        await bv.video_handler(make_request())

    response.prepare.assert_not_awaited()


@pytest.mark.asyncio
async def test_video_handler_401_with_bad_token_before_prepare(mocker) -> None:
    bv = make_basevideo(token="secret")
    response = MagicMock()
    response.prepare = AsyncMock()
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)

    with pytest.raises(web.HTTPUnauthorized):
        await bv.video_handler(make_request(headers={"Authorization": "Bearer wrong"}))

    response.prepare.assert_not_awaited()


@pytest.mark.asyncio
async def test_video_handler_accepts_valid_bearer(mocker) -> None:
    from aiohttp.client_exceptions import ClientConnectionResetError

    bv = make_basevideo(token="secret")
    response = MagicMock()
    response.prepare = AsyncMock()
    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)
    bv.image_jpeg = AsyncMock(return_value=(1, b"jpeg-bytes"))

    await bv.video_handler(make_request(headers={"Authorization": "Bearer secret"}))

    # auth passed: the stream was prepared and one frame written before the client reset
    response.prepare.assert_awaited_once()
    assert response.write.await_count == 1


@pytest.mark.asyncio
async def test_video_handler_accepts_valid_cookie(mocker) -> None:
    from aiohttp.client_exceptions import ClientConnectionResetError

    bv = make_basevideo(token="secret")
    response = MagicMock()
    response.prepare = AsyncMock()
    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)
    bv.image_jpeg = AsyncMock(return_value=(1, b"jpeg-bytes"))

    await bv.video_handler(make_request(cookies={_COOKIE_NAME: _session_value("secret")}))

    response.prepare.assert_awaited_once()
    assert response.write.await_count == 1


# raw_handler: unauthenticated requests must not wake the camera


@pytest.mark.asyncio
async def test_raw_handler_401_without_auth_does_not_activate_camera() -> None:
    bv = make_basevideo(token="secret")
    bv.activate_camera = AsyncMock()

    with pytest.raises(web.HTTPUnauthorized):
        await bv.raw_handler(make_request())

    bv.activate_camera.assert_not_awaited()


@pytest.mark.asyncio
async def test_raw_handler_401_with_bad_token_does_not_activate_camera() -> None:
    bv = make_basevideo(token="secret")
    bv.activate_camera = AsyncMock()

    with pytest.raises(web.HTTPUnauthorized):
        await bv.raw_handler(make_request(headers={"Authorization": "Bearer wrong"}))

    bv.activate_camera.assert_not_awaited()


# image_handler


@pytest.mark.asyncio
async def test_image_handler_401_without_auth() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    with pytest.raises(web.HTTPUnauthorized):
        await bv.image_handler(make_request("test.fits"))


@pytest.mark.asyncio
async def test_image_handler_401_with_wrong_token() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    with pytest.raises(web.HTTPUnauthorized):
        await bv.image_handler(make_request("test.fits", headers={"Authorization": "Bearer wrong"}))


@pytest.mark.asyncio
async def test_image_handler_accepts_valid_bearer() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    response = await bv.image_handler(make_request("test.fits", headers={"Authorization": "Bearer secret"}))

    assert response.status == 200
    assert response.body == b"fits-bytes"


@pytest.mark.asyncio
async def test_image_handler_accepts_valid_cookie() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    response = await bv.image_handler(make_request("test.fits", cookies={_COOKIE_NAME: _session_value("secret")}))

    assert response.status == 200
    assert response.body == b"fits-bytes"


# cookies: tampering, expiry, cross-token signature


@pytest.mark.asyncio
async def test_cookie_rejects_tampered_signature() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"
    value = _session_value("secret")
    tampered = value[:-1] + ("0" if value[-1] != "0" else "1")

    with pytest.raises(web.HTTPUnauthorized):
        await bv.image_handler(make_request("test.fits", cookies={_COOKIE_NAME: tampered}))


@pytest.mark.asyncio
async def test_cookie_rejects_expired_value() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    with pytest.raises(web.HTTPUnauthorized):
        await bv.image_handler(
            make_request("test.fits", cookies={_COOKIE_NAME: _session_value("secret", expiry=int(time.time()) - 3600)})
        )


@pytest.mark.asyncio
async def test_cookie_rejects_value_signed_with_other_token() -> None:
    bv = make_basevideo(token="secret")
    bv._cache["test.fits"] = b"fits-bytes"

    with pytest.raises(web.HTTPUnauthorized):
        await bv.image_handler(make_request("test.fits", cookies={_COOKIE_NAME: _session_value("other-token")}))


# login / logout


@pytest.mark.asyncio
async def test_login_handler_serves_form_without_authentication() -> None:
    bv = make_basevideo(token="secret")

    # no Authorization header, no session cookie -- must still succeed, since this is the
    # bootstrap page an unauthenticated browser needs before it can obtain a session
    response = await bv.login_handler(make_request())

    assert response.status == 200
    assert response.content_type == "text/html"
    assert "form" in response.text
    assert 'action="/login"' in response.text


@pytest.mark.asyncio
async def test_login_post_correct_token_sets_cookie_and_redirects() -> None:
    bv = make_basevideo(token="secret")
    request = make_request()
    request.post = AsyncMock(return_value={"token": "secret"})

    response = await bv.login_post_handler(request)

    assert response.status == 303
    assert response.headers["Location"] == "/"
    cookie = response._cookies[_COOKIE_NAME]
    assert cookie["max-age"] == str(24 * 60 * 60)
    assert cookie["path"] == "/"
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"


@pytest.mark.asyncio
async def test_login_post_wrong_token_returns_401(mocker) -> None:
    bv = make_basevideo(token="secret")
    request = make_request()
    request.post = AsyncMock(return_value={"token": "wrong"})
    mocker.patch("pyobs.modules.camera.basevideo.asyncio.sleep", AsyncMock())

    with pytest.raises(web.HTTPUnauthorized):
        await bv.login_post_handler(request)


@pytest.mark.asyncio
async def test_login_post_serializes_concurrent_failed_attempts(mocker) -> None:
    # regression test: concurrent failed attempts must be serialized through the sleep, so the
    # guess rate is capped regardless of concurrency -- not each sleeping independently in parallel
    mocker.patch("pyobs.modules.camera.basevideo._LOGIN_FAILURE_SLEEP", 0.05)
    bv = make_basevideo(token="secret")

    def make_wrong_request():
        request = make_request()
        request.post = AsyncMock(return_value={"token": "wrong"})
        return request

    start = time.monotonic()
    results = await asyncio.gather(
        bv.login_post_handler(make_wrong_request()),
        bv.login_post_handler(make_wrong_request()),
        return_exceptions=True,
    )
    elapsed = time.monotonic() - start

    assert all(isinstance(r, web.HTTPUnauthorized) for r in results)
    assert elapsed >= 0.09  # ~2x the sleep; would be ~0.05s if the two ran in parallel


@pytest.mark.asyncio
async def test_logout_clears_cookie_and_redirects_to_login() -> None:
    bv = make_basevideo(token="secret")

    response = await bv.logout_handler(make_request())

    assert response.status == 303
    assert response.headers["Location"] == "/login"
    cookie = response._cookies[_COOKIE_NAME]
    assert cookie["max-age"] == "0"


# ping stays open


@pytest.mark.asyncio
async def test_ping_handler_stays_open_with_token() -> None:
    bv = make_basevideo(token="secret")
    response = await bv.ping_handler(make_request())
    assert response.status == 200
