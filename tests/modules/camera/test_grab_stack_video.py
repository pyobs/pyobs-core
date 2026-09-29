"""Tests for BaseVideo.grab_stack(), the IDataStack implementation.

See specs/design/idatastack.md and specs/design/basevideo-grab-path.md.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import numpy as np
import pytest

import pyobs.utils.exceptions as exc
from pyobs.images import Image, ImageProcessor
from pyobs.interfaces import IDataStack
from pyobs.modules.camera.basevideo import BaseVideo
from pyobs.modules.camera.videoframes import Frame

# frame_number=False (with a filename pattern that doesn't need FRAMENUM): the per-frame
# FRAMENUM default does a real VFS read+write, which is both irrelevant here and, under this
# environment's default VFS root, occasionally slow enough to make these tests flaky
_TEST_FILENAMES = "/webcam/pyobs-{DAY-OBS|date:}-{DATE-OBS|time:}.fits"


class QueueVideo(BaseVideo):
    """Driver on the frames() contract whose frames come from a queue."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(frame_number=False, filenames=_TEST_FILENAMES, **kwargs)
        self.queue: asyncio.Queue[Frame] = asyncio.Queue()

    async def frames(self) -> AsyncIterator[Frame]:
        while True:
            yield await self.queue.get()


def make_video(cls: type[QueueVideo] = QueueVideo, **kwargs: Any) -> QueueVideo:
    video = cls(**kwargs)
    video.comm.set_state = AsyncMock()
    video.comm.set_capabilities = AsyncMock()
    video.request_fits_headers = AsyncMock(return_value={})
    return video


def stack_state_calls(video: BaseVideo) -> list[Any]:
    return [c.args[1] for c in video.comm.set_state.await_args_list if c.args[0] is IDataStack]


async def feed(video: QueueVideo, data: np.ndarray, delay: float = 0.02, **kwargs: Any) -> None:
    """Feed one frame that starts exposing now."""
    await asyncio.sleep(delay)
    await video.queue.put(Frame(data=data, start=time.time(), exposure_time=0.001, **kwargs))


async def feed_frames(video: QueueVideo, values: list[int], delay: float = 0.02) -> None:
    for value in values:
        await feed(video, np.full((4, 4), value, dtype=np.uint16), delay)


# ── happy path / first-frame semantics ─────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_starts_with_first_frame_started_after_call() -> None:
    """A frame that started exposing before grab_stack() was called is skipped; collection starts
    with the first frame that started afterwards."""
    video = make_video()
    await video.activate_camera()

    task = asyncio.create_task(video.grab_stack(3))
    await asyncio.sleep(0.02)
    await video.queue.put(Frame(np.full((4, 4), 10, dtype=np.uint16), start=time.time() - 1, exposure_time=0.001))
    await feed_frames(video, [20, 30, 40])

    filename = await asyncio.wait_for(task, timeout=10)
    data = video._cache[os.path.basename(filename)]
    image = Image.from_bytes(data)

    np.testing.assert_array_equal(image.data[:, 0, 0], [20, 30, 40])


@pytest.mark.asyncio
async def test_grab_stack_product_shape_and_headers() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(3))
    await feed_frames(video, [1, 2, 3, 4])

    filename = await asyncio.wait_for(task, timeout=10)
    data = video._cache[os.path.basename(filename)]
    image = Image.from_bytes(data)

    assert image.data.shape == (3, 4, 4)
    assert image.header["NAXIS3"] == 3
    assert image.header["CTYPE3"] == "FRAME"
    assert image.header["NFRAMES"] == 3
    assert image.header["PIPELINE"] == "none"
    assert image.frames is not None
    assert len(image.frames) == 3

    from pyobs.utils.time import Time

    assert Time(image.header["DATE-END"]) > Time(image.header["DATE-OBS"])


@pytest.mark.asyncio
async def test_grab_stack_requests_headers_once() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(3))
    await feed_frames(video, [1, 2, 3, 4])
    await asyncio.wait_for(task, timeout=10)

    video.request_fits_headers.assert_awaited_once()


@pytest.mark.asyncio
async def test_grab_stack_frames_are_copied() -> None:
    """cube[i] = data must copy, not alias -- a frame's array must not be able to change an
    already-collected frame."""
    video = make_video()

    task = asyncio.create_task(video.grab_stack(2))
    buf = np.full((4, 4), 1, dtype=np.uint16)
    await feed(video, buf)  # first collected frame -- written into cube[0]
    await asyncio.sleep(0.02)
    buf[:] = 99  # mutate the same array
    await feed(video, buf)  # second collected frame

    filename = await asyncio.wait_for(task, timeout=10)
    data = video._cache[os.path.basename(filename)]
    image = Image.from_bytes(data)

    assert image.data[0, 0, 0] == 1
    assert image.data[1, 0, 0] == 99


# ── validation / busy ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_count_zero_raises() -> None:
    video = make_video()
    with pytest.raises(exc.InvalidArgumentError):
        await video.grab_stack(0)


@pytest.mark.asyncio
async def test_grab_stack_second_call_while_running_raises_busy() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(3))
    await asyncio.sleep(0.02)

    with pytest.raises(exc.DeviceBusyError):
        await video.grab_stack(2)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_grab_data_during_stack_still_works() -> None:
    video = make_video()

    stack_task = asyncio.create_task(video.grab_stack(3))
    await asyncio.sleep(0.02)

    grab_task = asyncio.create_task(video.grab_data())
    await feed_frames(video, [1, 2, 3, 4, 5])

    await asyncio.wait_for(stack_task, timeout=10)
    filename = await asyncio.wait_for(grab_task, timeout=10)
    assert filename is not None


# ── memory cap ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_memory_cap_advisory_from_newest_frame() -> None:
    video = make_video(max_stack_bytes=100)
    await video._add_frame(Frame(np.zeros((4, 4), dtype=np.uint16)))

    with pytest.raises(exc.InvalidArgumentError):
        await video.grab_stack(5)

    # rejected before the stack was even started
    assert video._stack_abort is None


@pytest.mark.asyncio
async def test_grab_stack_memory_cap_authoritative_after_first_frame() -> None:
    video = make_video(max_stack_bytes=10)

    task = asyncio.create_task(video.grab_stack(3))
    await feed_frames(video, [1, 2])

    with pytest.raises(exc.InvalidArgumentError):
        await asyncio.wait_for(task, timeout=10)


# ── color frame ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_color_frame_raises_grabimageerror() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(3))
    await feed(video, np.ones((3, 4, 4), dtype=np.uint16))

    with pytest.raises(exc.GrabImageError):
        await asyncio.wait_for(task, timeout=10)


# ── dropped frames / settings changes ────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_fails_when_frames_were_dropped() -> None:
    video = make_video(buffer_frames=2)

    task = asyncio.create_task(video.grab_stack(5))
    await feed_frames(video, [1])
    await asyncio.sleep(0.02)

    # three frames in a row without giving the stack a chance to run: one falls out of the buffer
    for value in (2, 3, 4):
        await video._add_frame(Frame(np.full((4, 4), value, dtype=np.uint16), exposure_time=0.001))

    with pytest.raises(exc.GrabImageError, match="dropped"):
        await asyncio.wait_for(task, timeout=10)


@pytest.mark.asyncio
async def test_grab_stack_fails_when_settings_change() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(3))
    await feed_frames(video, [1])
    await asyncio.sleep(0.02)
    video._new_generation()
    await feed_frames(video, [2])

    with pytest.raises(exc.GrabImageError, match="settings changed"):
        await asyncio.wait_for(task, timeout=10)


# ── abort ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_abort_mid_stack() -> None:
    video = make_video()

    task = asyncio.create_task(video.grab_stack(5))
    await feed_frames(video, [1, 2])
    await video.abort()

    with pytest.raises(exc.AbortedError):
        await asyncio.wait_for(task, timeout=10)

    assert video._stack_abort is None
    last_state = stack_state_calls(video)[-1]
    assert (last_state.count_total, last_state.count_left) == (0, 0)


@pytest.mark.asyncio
async def test_abort_without_running_stack_is_a_noop() -> None:
    video = make_video()
    await video.abort()  # must not raise


# ── keep-alive ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_keeps_camera_active(mocker) -> None:
    video = make_video(sleep_time=0)
    deactivate = mocker.patch.object(video, "_deactivate_camera", new=AsyncMock())

    task = asyncio.create_task(video.grab_stack(3))
    # the 1s keep-alive activate_camera() calls in grab_stack()'s wait loop only matter for a
    # stack that runs longer than sleep_time; feed frames quickly here and just check the
    # camera never went inactive while the stack was running
    await feed_frames(video, [1, 2, 3, 4], delay=0.01)
    await asyncio.wait_for(task, timeout=10)

    deactivate.assert_not_called()


# ── pipeline on the cube ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_pipeline_runs_after_finish_image_override_headers() -> None:
    class _TaggingVideo(QueueVideo):
        async def _finish_image(self, image: Image, broadcast: bool, image_type: Any) -> tuple[Image, str]:
            image.header["CUSTOM"] = True
            return await super()._finish_image(image, broadcast, image_type)

    class _RequireHeaderStep(ImageProcessor):
        async def __call__(self, image: Image) -> Image:
            if "CUSTOM" not in image.header:
                raise exc.ImageError("CUSTOM header not set yet")
            image.data = image.data.mean(axis=0).astype(image.data.dtype)
            del image.header["CTYPE3"]
            del image.header["NAXIS3"]
            return image

    video = make_video(_TaggingVideo, pipelines={"mean": [_RequireHeaderStep()]}, default_pipeline="mean")

    task = asyncio.create_task(video.grab_stack(3))
    await feed_frames(video, [1, 2, 3, 4])

    filename = await asyncio.wait_for(task, timeout=10)
    data = video._cache[os.path.basename(filename)]
    image = Image.from_bytes(data)

    assert image.data.ndim == 2
    assert image.header["PIPELINE"] == "mean"
