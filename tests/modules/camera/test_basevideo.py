from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from aiohttp import web

from pyobs.comm import Comm
from pyobs.events import NewImageEvent
from pyobs.interfaces import IImageType, IVideo
from pyobs.modules import Module
from pyobs.modules.camera.basevideo import _COOKIE_NAME, BaseVideo, NextImage
from pyobs.modules.camera.videoframes import Frame, FrameRecord, StartSource
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ImageType
from pyobs.utils.stretch import StretchParams


def make_basevideo(**kwargs) -> BaseVideo:
    comm = MagicMock(spec=Comm)
    return BaseVideo(comm=comm, **kwargs)


def make_request(
    filename: str | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
) -> MagicMock:
    request = MagicMock()
    request.query = query or {}
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

    video_calls = [c for c in bv._comm.set_capabilities.await_args_list if c.args[0] is IVideo]
    assert len(video_calls) == 1
    interface, caps = video_calls[0].args
    assert interface is IVideo
    assert caps.mjpeg == bv._video_path
    assert caps.raw == bv._raw_path

    image_type_calls = [c for c in bv._comm.set_state.await_args_list if c.args[0] is IImageType]
    assert len(image_type_calls) == 1
    state_interface, state = image_type_calls[0].args
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
async def test_image_jpeg_returns_none_when_no_frame() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()

    num, jpeg = await bv.image_jpeg()

    bv.activate_camera.assert_awaited_once()
    assert num is None
    assert jpeg is None


@pytest.mark.asyncio
async def test_image_jpeg_returns_newest_frame_as_jpeg() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))
    await bv._add_frame(Frame(np.ones((4, 4), dtype=np.uint16)))

    num, jpeg = await bv.image_jpeg()

    assert num == 1
    assert jpeg is not None and jpeg.startswith(b"\xff\xd8")


# ── create_jpeg ─────────────────────────────────────────────────────────────


def test_create_jpeg_converts_uint16() -> None:
    data = np.full((4, 4), 40000, dtype=np.uint16)
    jpeg = BaseVideo.create_jpeg(data)
    assert jpeg.startswith(b"\xff\xd8")  # JPEG magic bytes


def test_create_jpeg_handles_uint8() -> None:
    data = np.full((4, 4), 200, dtype=np.uint8)
    jpeg = BaseVideo.create_jpeg(data)
    assert jpeg.startswith(b"\xff\xd8")


def test_create_jpeg_applies_stretch_params() -> None:
    data = np.arange(64, dtype=np.uint16).reshape(8, 8)
    linear = BaseVideo.create_jpeg(data, StretchParams(cuts="full"))
    stretched = BaseVideo.create_jpeg(data, StretchParams(stretch="asinh", cuts="minmax"))
    assert linear != stretched


def test_init_rejects_invalid_stretch_defaults() -> None:
    with pytest.raises(ValueError):
        make_basevideo(stretch="nonsense")
    with pytest.raises(ValueError):
        make_basevideo(jpeg_quality=0)


# ── frame buffer: _add_frame / _set_image / frames() ────────────────────────


@pytest.mark.asyncio
async def test_add_frame_numbers_frames_and_stores_them() -> None:
    bv = make_basevideo()

    await bv._add_frame(Frame(np.zeros((4, 4))))
    record = await bv._add_frame(Frame(np.ones((4, 4))))

    assert record.number == 1
    assert bv._frame_num == 2
    assert bv._frames.latest() is record


@pytest.mark.asyncio
async def test_add_frame_flips_when_configured() -> None:
    bv = make_basevideo(flip=True)
    data = np.arange(16).reshape(4, 4).astype(float)

    record = await bv._add_frame(Frame(data))

    np.testing.assert_array_equal(record.data, np.flip(data, axis=0))


@pytest.mark.asyncio
async def test_add_frame_start_time_sources() -> None:
    bv = make_basevideo(readout_time=0.5)

    device = await bv._add_frame(Frame(np.zeros((2, 2)), start=100.0, exposure_time=2.0))
    estimated = await bv._add_frame(Frame(np.zeros((2, 2)), exposure_time=2.0))
    unknown = await bv._add_frame(Frame(np.zeros((2, 2))))

    assert device.start == 100.0 and device.start_source == StartSource.DEVICE
    assert estimated.start_source == StartSource.ESTIMATED
    assert estimated.start == pytest.approx(estimated.arrival - 2.5)
    assert unknown.start is None and unknown.start_source == StartSource.UNKNOWN


@pytest.mark.asyncio
async def test_add_frame_uses_current_generation_unless_given() -> None:
    bv = make_basevideo()
    bv._new_generation()

    implicit = await bv._add_frame(Frame(np.zeros((2, 2))))
    explicit = await bv._add_frame(Frame(np.zeros((2, 2)), generation=0))

    assert implicit.generation == 1
    assert explicit.generation == 0


@pytest.mark.asyncio
async def test_set_image_shim_feeds_buffer_with_estimated_start() -> None:
    bv = make_basevideo()
    bv._exposure_time = 0.5  # type: ignore[attr-defined]

    await bv._set_image(np.zeros((4, 4)))

    record = bv._frames.latest()
    assert record is not None
    assert record.exposure_time == 0.5
    assert record.start_source == StartSource.ESTIMATED


class _IteratorVideo(BaseVideo):
    """Driver on the frames() contract, fed from a queue; records when acquisition stops."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(comm=MagicMock(spec=Comm), **kwargs)
        self.queue: asyncio.Queue[Frame | Exception] = asyncio.Queue()
        self.stopped = 0

    async def frames(self) -> AsyncIterator[Frame]:
        try:
            while True:
                item = await self.queue.get()
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            self.stopped += 1


@pytest.mark.asyncio
async def test_frames_iterator_runs_while_active_and_is_closed_on_deactivate() -> None:
    bv = _IteratorVideo()

    await bv.activate_camera()
    await bv.queue.put(Frame(np.zeros((2, 2))))
    await asyncio.sleep(0.01)
    assert bv._frames.last_number == 0

    await bv.deactivate_camera()
    assert bv.stopped == 1
    assert bv._frame_loop_task is None


@pytest.mark.asyncio
async def test_frames_iterator_is_restarted_after_error(mocker) -> None:
    mocker.patch("pyobs.modules.camera.basevideo._FRAME_LOOP_MIN_BACKOFF", 0.01)
    bv = _IteratorVideo()

    await bv.activate_camera()
    await bv.queue.put(RuntimeError("usb hiccup"))
    await bv.queue.put(Frame(np.zeros((2, 2))))
    await asyncio.sleep(0.1)

    assert bv.stopped >= 1
    assert bv._frames.last_number == 0
    await bv.deactivate_camera()


@pytest.mark.asyncio
async def test_no_frame_loop_without_frames_iterator() -> None:
    bv = make_basevideo()
    await bv.activate_camera()
    assert bv._frame_loop_task is None


# ── _create_image ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_image_sets_headers_and_delegates_to_finish() -> None:
    bv = make_basevideo()
    bv.add_requested_fits_headers = AsyncMock()
    bv.add_fits_headers = AsyncMock()
    bv._finish_image = AsyncMock(return_value=("image", "filename.fits"))
    next_image = NextImage(
        date_obs="2024-01-01T00:00:00",
        image_type=ImageType.DARK,
        header_futures={},
        broadcast=False,
        pipeline=None,
        exposure_time=2.0,
        date_src=StartSource.ESTIMATED,
        frame_number=7,
    )

    result = await bv._create_image(np.zeros((4, 4)), next_image)

    assert result == ("image", "filename.fits")
    bv.add_requested_fits_headers.assert_awaited_once()
    bv.add_fits_headers.assert_awaited_once()
    image_arg = bv.add_requested_fits_headers.await_args[0][0]
    assert image_arg.header["DATE-OBS"] == "2024-01-01T00:00:00"
    assert image_arg.header["IMAGETYP"] == ImageType.DARK
    assert image_arg.header["EXPTIME"] == 2.0
    assert image_arg.header["DATE-SRC"] == "estimated"
    assert image_arg.header["VIDFRAME"] == 7
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


def _grab_ready(bv: BaseVideo) -> None:
    bv.activate_camera = AsyncMock()
    bv.request_fits_headers = AsyncMock(return_value={})
    bv._create_image = AsyncMock(side_effect=lambda data, next_image: ("image", f"frame-{next_image.frame_number}"))


@pytest.mark.asyncio
async def test_grab_data_returns_first_frame_started_after_request() -> None:
    bv = make_basevideo()
    _grab_ready(bv)

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    t_request = time.time() - 0.005

    # frame 0 was exposing when the request came in (started before it), frame 1 wasn't
    await bv._add_frame(Frame(np.zeros((2, 2)), start=t_request - 1.0, exposure_time=1.0))
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01))

    assert await asyncio.wait_for(task, timeout=2) == "frame-1"


@pytest.mark.asyncio
async def test_grab_data_ignores_frames_already_in_buffer() -> None:
    bv = make_basevideo()
    _grab_ready(bv)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time() - 1.0, exposure_time=0.5))

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01))

    assert await asyncio.wait_for(task, timeout=2) == "frame-1"


@pytest.mark.asyncio
async def test_grab_data_late_request_does_not_get_frame_exposing_at_request_time() -> None:
    """Regression for the late-joiner bug (#925): a request arriving while a frame is already
    exposing must not be served that frame, even if an earlier request is."""
    bv = make_basevideo()
    _grab_ready(bv)

    early = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    frame0_start = time.time()
    await asyncio.sleep(0.01)
    late = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)

    await bv._add_frame(Frame(np.zeros((2, 2)), start=frame0_start, exposure_time=0.02))
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.02))

    assert await asyncio.wait_for(early, timeout=2) == "frame-0"
    assert await asyncio.wait_for(late, timeout=2) == "frame-1"


@pytest.mark.asyncio
async def test_grab_data_estimated_start_needs_one_frame_margin() -> None:
    bv = make_basevideo()
    _grab_ready(bv)

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    # estimated start = arrival - 0.5s, i.e. before the request: could be a queued frame
    await bv._add_frame(Frame(np.zeros((2, 2)), exposure_time=0.5))
    await asyncio.sleep(0.01)
    assert not task.done()

    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time() + 1.0, exposure_time=0.5))
    assert await asyncio.wait_for(task, timeout=2) == "frame-1"


@pytest.mark.asyncio
async def test_grab_data_unknown_start_skips_frame_in_progress() -> None:
    bv = make_basevideo()
    _grab_ready(bv)
    await bv._add_frame(Frame(np.zeros((2, 2))))  # frame 0, before the request

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2))))  # frame 1, was exposing at request time
    await asyncio.sleep(0.01)
    assert not task.done()
    await bv._add_frame(Frame(np.zeros((2, 2))))  # frame 2

    assert await asyncio.wait_for(task, timeout=2) == "frame-2"


@pytest.mark.asyncio
async def test_grab_data_waits_for_current_settings_generation() -> None:
    bv = make_basevideo()
    _grab_ready(bv)
    bv._new_generation()

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01, generation=0))
    await asyncio.sleep(0.01)
    assert not task.done()
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01, generation=1))

    assert await asyncio.wait_for(task, timeout=2) == "frame-1"


@pytest.mark.asyncio
async def test_grab_data_requests_headers_at_request_time() -> None:
    bv = make_basevideo()
    _grab_ready(bv)

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    bv.request_fits_headers.assert_awaited_once()
    task.cancel()


@pytest.mark.asyncio
async def test_frames_keep_flowing_while_grab_data_builds_image() -> None:
    """A slow image build (e.g. a peer not answering its FITS header request) must not stall the
    frame buffer, unlike the old _set_image()-based handoff."""
    bv = make_basevideo()
    _grab_ready(bv)
    release = asyncio.Event()

    async def slow_create(data: Any, next_image: NextImage) -> tuple[str, str]:
        await release.wait()
        return "image", "slow.fits"

    bv._create_image = slow_create  # type: ignore[method-assign]

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01))
    await asyncio.sleep(0.01)

    # grab_data() is now stuck building the image; frames still go into the buffer
    for _ in range(3):
        await asyncio.wait_for(bv._add_frame(Frame(np.zeros((2, 2)))), timeout=0.5)
    assert bv._frames.last_number == 3

    release.set()
    assert await asyncio.wait_for(task, timeout=2) == "slow.fits"


@pytest.mark.asyncio
async def test_grab_data_wraps_unexpected_errors() -> None:
    bv = make_basevideo()
    _grab_ready(bv)
    bv._create_image = AsyncMock(side_effect=RuntimeError("pipeline broke"))

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01))

    with pytest.raises(exc.GrabImageError):
        await asyncio.wait_for(task, timeout=2)


@pytest.mark.asyncio
async def test_grab_data_passes_pyobs_errors_through() -> None:
    bv = make_basevideo()
    _grab_ready(bv)
    bv._create_image = AsyncMock(side_effect=exc.ImageError("bad"))

    task = asyncio.create_task(bv.grab_data())
    await asyncio.sleep(0.01)
    await bv._add_frame(Frame(np.zeros((2, 2)), start=time.time(), exposure_time=0.01))

    with pytest.raises(exc.ImageError):
        await asyncio.wait_for(task, timeout=2)


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


def _no_exposure_record(data: np.ndarray, number: int = 0) -> FrameRecord:
    return FrameRecord(
        number=number,
        data=data,
        arrival=1700000000.0,
        start=1699999999.0,
        start_source=StartSource.DEVICE,
        exposure_time=1.0,
        generation=3,
    )


def test_raw_frame_meta_and_little_endian_bytes() -> None:
    bv = make_basevideo()
    data = np.arange(6, dtype=np.uint16).reshape(2, 3)

    meta_bytes, frame = bv._raw_frame(_no_exposure_record(data, number=5))

    meta = json.loads(meta_bytes)
    assert meta["DTYPE"] == "<u2"
    assert meta["NAXIS1"] == 3
    assert meta["NAXIS2"] == 2
    assert "DATE-OBS" in meta
    assert "IMAGETYP" in meta
    assert meta["VIDFRAME"] == 5
    assert meta["DATE-SRC"] == "device"
    assert meta["EXPTIME"] == 1.0
    assert meta["SETGEN"] == 3
    assert (meta["CROP-X"], meta["CROP-Y"], meta["SWBIN"]) == (0, 0, 1)
    # little-endian: value 0 -> 00 00, value 1 -> 01 00
    assert frame == data.astype("<u2").tobytes()
    assert frame[:4] == b"\x00\x00\x01\x00"


def test_raw_frame_crop_and_binning() -> None:
    bv = make_basevideo()
    data = np.arange(100, dtype=np.uint16).reshape(10, 10)

    meta_bytes, frame = bv._raw_frame(_no_exposure_record(data), crop=(2, 4, 4, 4), binning=2)

    meta = json.loads(meta_bytes)
    assert (meta["NAXIS1"], meta["NAXIS2"]) == (2, 2)
    assert (meta["CROP-X"], meta["CROP-Y"], meta["SWBIN"]) == (2, 4, 2)
    assert meta["XORGSUBF"] == 2 and meta["YORGSUBF"] == 4
    expected = data[4:8, 2:6].astype(np.float32).reshape(2, 2, 2, 2).mean(axis=(1, 3))
    np.testing.assert_array_equal(np.frombuffer(frame, dtype=meta["DTYPE"]).reshape(2, 2), expected)


def test_raw_frame_crop_is_clipped_and_empty_crop_raises() -> None:
    bv = make_basevideo()
    data = np.zeros((10, 10), dtype=np.uint16)

    meta, _ = bv._raw_frame(_no_exposure_record(data), crop=(8, 8, 5, 5))
    assert (json.loads(meta)["NAXIS1"], json.loads(meta)["NAXIS2"]) == (2, 2)

    with pytest.raises(ValueError):
        bv._raw_frame(_no_exposure_record(data), crop=(20, 20, 5, 5))


@pytest.mark.parametrize(
    "query",
    [
        {"x": "1"},
        {"x": "a", "y": "0", "w": "1", "h": "1"},
        {"x": "0", "y": "0", "w": "0", "h": "1"},
        {"bin": "0"},
        {"max_rate": "-1"},
    ],
)
def test_parse_raw_params_rejects_invalid(query: dict[str, str]) -> None:
    with pytest.raises(web.HTTPBadRequest):
        BaseVideo._parse_raw_params(make_request(query=query))


def test_parse_raw_params_valid() -> None:
    crop, binning, rate = BaseVideo._parse_raw_params(
        make_request(query={"x": "1", "y": "2", "w": "3", "h": "4", "bin": "2", "max_rate": "5"})
    )
    assert crop == (1, 2, 3, 4) and binning == 2 and rate == 5.0


def _one_shot_response(mocker) -> MagicMock:
    from aiohttp.client_exceptions import ClientConnectionResetError

    response = MagicMock()
    response.prepare = AsyncMock()
    response.write = AsyncMock(side_effect=ClientConnectionResetError())
    mocker.patch("pyobs.modules.camera.basevideo.web.StreamResponse", return_value=response)
    return response


@pytest.mark.asyncio
async def test_raw_handler_sends_newest_frame_and_keeps_active(mocker) -> None:
    bv = make_basevideo()

    # several frames arriving before the handler starts: latest wins
    for i in range(3):
        await bv._add_frame(Frame(np.full((4, 4), i, dtype=np.uint16)))

    response = _one_shot_response(mocker)

    await bv.raw_handler(make_request())

    assert response.write.await_count == 1
    assert b'"VIDFRAME":2' in response.write.await_args.args[0]
    assert bv.camera_active is True
    assert bv._active_time > 0


@pytest.mark.asyncio
async def test_raw_handler_bad_params_rejected_before_activation() -> None:
    bv = make_basevideo()
    bv.activate_camera = AsyncMock()

    with pytest.raises(web.HTTPBadRequest):
        await bv.raw_handler(make_request(query={"bin": "0"}))

    bv.activate_camera.assert_not_awaited()


@pytest.mark.asyncio
async def test_raw_handler_touches_activity_without_new_frame(mocker) -> None:
    # no frame has arrived yet -- the wait must time out and re-touch activity
    # anyway, per design doc §5, instead of blocking indefinitely
    bv = make_basevideo(sleep_time=0.02)
    response = _one_shot_response(mocker)

    real_activate = bv.activate_camera
    activate_calls = 0

    async def activate_side_effect() -> None:
        nonlocal activate_calls
        activate_calls += 1
        await real_activate()
        if activate_calls == 2:
            # this is the timeout-triggered re-touch with no frame yet produced;
            # now produce one so the next loop iteration can wake normally
            await bv._add_frame(Frame(np.zeros((2, 2), dtype=np.uint16)))

    bv.activate_camera = activate_side_effect  # type: ignore[method-assign]

    await bv.raw_handler(make_request())

    assert activate_calls >= 2
    assert response.write.await_count == 1
    assert bv.camera_active is True


@pytest.mark.asyncio
async def test_raw_handler_dedupes_frame_build_across_consumers(mocker) -> None:
    # two raw clients reading the same frame in the same crop must not each pay for the header
    # build/JSON serialization/tobytes() copy -- only the first computes it (#769)
    bv = make_basevideo()
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))

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

    await asyncio.wait_for(asyncio.gather(bv.raw_handler(make_request()), bv.raw_handler(make_request())), timeout=2)

    assert raw_frame_spy.call_count == 1
    assert len(responses) == 2
    assert responses[0].write.await_args.args == responses[1].write.await_args.args


@pytest.mark.asyncio
async def test_raw_handler_builds_separately_per_crop(mocker) -> None:
    bv = make_basevideo()
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))
    _one_shot_response(mocker)
    raw_frame_spy = mocker.spy(bv, "_raw_frame")

    await bv.raw_handler(make_request())
    await bv.raw_handler(make_request(query={"x": "0", "y": "0", "w": "2", "h": "2"}))

    assert raw_frame_spy.call_count == 2


@pytest.mark.asyncio
async def test_raw_handler_recomputes_after_new_frame(mocker) -> None:
    # the cache must not serve stale bytes once a new frame has arrived
    bv = make_basevideo()
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))
    _one_shot_response(mocker)
    raw_frame_spy = mocker.spy(bv, "_raw_frame")

    await bv.raw_handler(make_request())
    await bv._add_frame(Frame(np.ones((4, 4), dtype=np.uint16)))
    await bv.raw_handler(make_request())

    assert raw_frame_spy.call_count == 2


# ── MJPEG live view ─────────────────────────────────────────────────────────


def test_parse_jpeg_params_defaults_and_overrides() -> None:
    bv = make_basevideo(stretch="sqrt", cuts="percentile", cut_lo=1.0, cut_hi=99.0, jpeg_quality=70)

    params, quality = bv._parse_jpeg_params(make_request())
    assert params == StretchParams(stretch="sqrt", cuts="percentile", lo=1.0, hi=99.0)
    assert quality == 70

    params, quality = bv._parse_jpeg_params(
        make_request(
            query={"stretch": "asinh", "cuts": "manual", "lo": "10", "hi": "20", "scale": "2", "quality": "50"}
        )
    )
    assert params == StretchParams(stretch="asinh", cuts="manual", lo=10.0, hi=20.0, scale=2)
    assert quality == 50


@pytest.mark.parametrize(
    "query", [{"stretch": "nope"}, {"cuts": "manual"}, {"scale": "0"}, {"quality": "100"}, {"lo": "abc"}]
)
def test_parse_jpeg_params_rejects_invalid(query: dict[str, str]) -> None:
    bv = make_basevideo()
    with pytest.raises(web.HTTPBadRequest):
        bv._parse_jpeg_params(make_request(query=query))


@pytest.mark.asyncio
async def test_video_handler_shares_encoding_per_setting(mocker) -> None:
    bv = make_basevideo()
    await bv._add_frame(Frame(np.arange(16, dtype=np.uint16).reshape(4, 4)))
    _one_shot_response(mocker)
    encode_spy = mocker.spy(BaseVideo, "create_jpeg")

    await bv.video_handler(make_request())
    await bv.video_handler(make_request())
    assert encode_spy.call_count == 1

    await bv.video_handler(make_request(query={"stretch": "asinh"}))
    assert encode_spy.call_count == 2


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
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))

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
    await bv._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))

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
