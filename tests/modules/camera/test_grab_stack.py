"""Tests for BaseCamera.grab_stack(), the IDataStack implementation.

See specs/design/idatastack.md.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import numpy as np
import pytest

import pyobs.utils.exceptions as exc
from pyobs.images import Image, ImageProcessor
from pyobs.images.processors.stack import MedianStack
from pyobs.interfaces import IDataStack
from pyobs.modules.camera import DummyCamera
from pyobs.modules.camera.basecamera import calc_stack_timeout
from pyobs.utils.enums import ExposureStatus

# frame_number=False (with a filename pattern that doesn't need FRAMENUM): the per-frame
# FRAMENUM default does a real VFS read+write, which is both irrelevant here and, under this
# environment's default VFS root, occasionally slow enough to make these tests flaky
_TEST_FILENAMES = "/cache/pyobs-{DAY-OBS|date:}-{DATE-OBS|time:}-{IMAGETYP|type}00.fits.gz"


class MeanCombine(ImageProcessor):
    """Test processor: collapses a cube to 2D via a mean, like a real CombineStack would."""

    async def __call__(self, image: Image) -> Image:
        image.data = image.data.mean(axis=0).astype(image.data.dtype)
        if "CTYPE3" in image.header:
            del image.header["CTYPE3"]
        if "NAXIS3" in image.header:
            del image.header["NAXIS3"]
        return image


def make_camera(**kwargs: Any) -> DummyCamera:
    camera = DummyCamera(readout_time=0, image_size=(20, 20), frame_number=False, filenames=_TEST_FILENAMES, **kwargs)
    camera.comm.set_state = AsyncMock()
    camera.comm.set_capabilities = AsyncMock()
    camera.vfs.write_image = AsyncMock()
    return camera


def stack_state_calls(camera: DummyCamera) -> list[Any]:
    return [c.args[1] for c in camera.comm.set_state.await_args_list if c.args[0] is IDataStack]


# ── happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_without_pipeline() -> None:
    camera = make_camera()
    await camera.open()
    camera.comm.set_state.reset_mock()

    filename = await camera.grab_stack(3)

    assert filename is not None
    camera.vfs.write_image.assert_awaited_once()
    written_filename, image = camera.vfs.write_image.await_args[0]
    assert written_filename == filename

    assert image.data.shape == (3, 20, 20)
    assert image.header["NAXIS3"] == 3
    assert image.header["CTYPE3"] == "FRAME"
    assert image.header["NFRAMES"] == 3
    assert image.header["PIPELINE"] == "none"

    assert image.frames is not None
    assert len(image.frames) == 3

    from pyobs.utils.time import Time

    assert Time(image.header["DATE-END"]) > Time(image.header["DATE-OBS"])


@pytest.mark.asyncio
async def test_grab_stack_count_one_is_still_3d() -> None:
    camera = make_camera()
    await camera.open()

    await camera.grab_stack(1)

    image = camera.vfs.write_image.await_args[0][1]
    assert image.data.shape == (1, 20, 20)
    assert image.header["NAXIS3"] == 1


@pytest.mark.asyncio
async def test_grab_stack_count_zero_raises() -> None:
    camera = make_camera()
    await camera.open()

    with pytest.raises(exc.InvalidArgumentError):
        await camera.grab_stack(0)


# ── busy checks ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_busy_while_exposing() -> None:
    camera = make_camera()
    await camera.open()
    camera._camera_status = ExposureStatus.EXPOSING

    with pytest.raises(exc.DeviceBusyError):
        await camera.grab_stack(3)


@pytest.mark.asyncio
async def test_grab_stack_busy_while_sequence_running() -> None:
    camera = make_camera()
    await camera.open()
    camera._sequence_count_left = 3

    with pytest.raises(exc.DeviceBusyError):
        await camera.grab_stack(3)


@pytest.mark.asyncio
async def test_grab_stack_busy_while_another_stack_running() -> None:
    camera = make_camera()
    await camera.open()
    camera._stack_running = True

    with pytest.raises(exc.DeviceBusyError):
        await camera.grab_stack(3)


@pytest.mark.asyncio
async def test_grab_sequence_busy_while_stack_running() -> None:
    camera = make_camera()
    await camera.open()
    camera._stack_running = True
    camera._camera_status = ExposureStatus.EXPOSING

    with pytest.raises(exc.DeviceBusyError):
        await camera.grab_sequence(3)


# ── header requests / _init_exposure ────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_requests_headers_exactly_twice() -> None:
    camera = make_camera()
    await camera.open()
    camera.request_fits_headers = AsyncMock(return_value={})

    await camera.grab_stack(3)

    assert camera.request_fits_headers.await_count == 2
    camera.request_fits_headers.assert_any_await(before=True)
    camera.request_fits_headers.assert_any_await(before=False)


@pytest.mark.asyncio
async def test_grab_stack_calls_init_exposure_once() -> None:
    camera = make_camera()
    await camera.open()
    camera._init_exposure = AsyncMock()

    await camera.grab_stack(3)

    camera._init_exposure.assert_awaited_once()


# ── memory cap ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_memory_cap_after_first_frame() -> None:
    camera = make_camera(max_stack_bytes=100)
    await camera.open()

    with pytest.raises(exc.InvalidArgumentError):
        await camera.grab_stack(3)

    camera.vfs.write_image.assert_not_called()


@pytest.mark.asyncio
async def test_grab_stack_memory_cap_advisory_before_any_exposure() -> None:
    camera = make_camera(max_stack_bytes=100)
    await camera.open()
    camera._last_frame_nbytes = 1000

    expose_spy = AsyncMock(side_effect=AssertionError("should not have exposed"))
    camera._expose = expose_spy

    with pytest.raises(exc.InvalidArgumentError):
        await camera.grab_stack(3)

    expose_spy.assert_not_called()


# ── shape/dtype mismatch, color frames ──────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_shape_mismatch_raises_grabimageerror() -> None:
    camera = make_camera()
    await camera.open()

    original_expose = camera._expose
    call_count = 0

    async def flaky_expose(*args: Any, **kwargs: Any) -> Image:
        nonlocal call_count
        call_count += 1
        image = await original_expose(*args, **kwargs)
        if call_count == 2:
            image.data = np.ones((5, 5))
        return image

    camera._expose = flaky_expose

    with pytest.raises(exc.GrabImageError):
        await camera.grab_stack(3)

    camera.vfs.write_image.assert_not_called()


@pytest.mark.asyncio
async def test_grab_stack_color_frame_raises_grabimageerror() -> None:
    camera = make_camera()
    await camera.open()

    original_expose = camera._expose

    async def color_expose(*args: Any, **kwargs: Any) -> Image:
        image = await original_expose(*args, **kwargs)
        image.data = np.ones((3, 20, 20))
        return image

    camera._expose = color_expose

    with pytest.raises(exc.GrabImageError):
        await camera.grab_stack(2)

    camera.vfs.write_image.assert_not_called()


# ── abort ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_abort_during_frame() -> None:
    camera = make_camera()
    await camera.open()
    await camera.set_exposure_time(0.5)

    task = asyncio.create_task(camera.grab_stack(5))
    await asyncio.sleep(0.05)
    await camera.abort()

    with pytest.raises(exc.AbortedError):
        await task

    camera.vfs.write_image.assert_not_called()
    assert camera._camera_status == ExposureStatus.IDLE
    last_state = stack_state_calls(camera)[-1]
    assert (last_state.count_total, last_state.count_left) == (0, 0)


@pytest.mark.asyncio
async def test_grab_stack_abort_between_frames() -> None:
    """abort() landing in the gap between two frames (rather than during _expose() itself)
    must still be caught -- this is exactly why grab_stack keeps its own _stack_abort flag
    separate from expose_abort, which gets cleared at the start of every frame."""
    camera = make_camera()
    await camera.open()

    original_expose = camera._expose
    call_count = 0

    async def expose_then_abort(*args: Any, **kwargs: Any) -> Image:
        nonlocal call_count
        call_count += 1
        image = await original_expose(*args, **kwargs)
        if call_count == 1:
            # simulate abort() landing right after frame 1 finished, before frame 2 starts
            camera._stack_abort = True
        return image

    camera._expose = expose_then_abort

    with pytest.raises(exc.AbortedError):
        await camera.grab_stack(5)

    camera.vfs.write_image.assert_not_called()
    assert camera._camera_status == ExposureStatus.IDLE


@pytest.mark.asyncio
async def test_grab_stack_state_published_with_decreasing_count_left() -> None:
    camera = make_camera()
    await camera.open()
    camera.comm.set_state.reset_mock()

    await camera.grab_stack(3)

    states = stack_state_calls(camera)
    assert states[0].count_total == 3 and states[0].count_left == 3
    assert states[-1].count_total == 0 and states[-1].count_left == 0
    left_values = [s.count_left for s in states[:-1]]
    assert left_values == sorted(left_values, reverse=True)


@pytest.mark.asyncio
async def test_grab_stack_state_ends_idle_on_error() -> None:
    camera = make_camera(max_stack_bytes=100)
    await camera.open()
    camera.comm.set_state.reset_mock()

    with pytest.raises(exc.InvalidArgumentError):
        await camera.grab_stack(3)

    states = stack_state_calls(camera)
    assert states[-1].count_total == 0 and states[-1].count_left == 0


# ── pipeline on the cube ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grab_stack_with_combine_pipeline_stores_2d_product() -> None:
    camera = make_camera(pipelines={"mean": [MeanCombine()]}, default_pipeline="mean")
    await camera.open()

    filename = await camera.grab_stack(3)

    assert filename is not None
    image = camera.vfs.write_image.await_args[0][1]
    assert image.data.ndim == 2
    assert image.header["PIPELINE"] == "mean"


@pytest.mark.asyncio
async def test_grab_stack_with_median_stack_pipeline() -> None:
    camera = make_camera(pipelines={"median": [MedianStack()]}, default_pipeline="median")
    await camera.open()

    await camera.grab_stack(3)

    image = camera.vfs.write_image.await_args[0][1]
    assert image.data.shape == (20, 20)
    assert image.data.dtype == np.float32
    assert image.header["COMBMETH"] == "median"
    assert image.header["NFRAMES"] == 3
    assert "CTYPE3" not in image.header
    assert len(image.frames) == 3


# ── calc_stack_timeout ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calc_stack_timeout_formula() -> None:
    camera = make_camera(stack_frame_overhead=10.0, stack_timeout_margin=60.0)
    await camera.set_exposure_time(5.0)

    timeout_value = await calc_stack_timeout(camera, count=4)

    assert timeout_value == 4 * (5.0 + 10.0) + 60.0
