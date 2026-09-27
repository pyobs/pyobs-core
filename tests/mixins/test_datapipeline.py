"""Tests for IDataPipeline / DataPipelineMixin, plus its wiring into BaseCamera and BaseVideo.

See specs/design/idatapipeline.md.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock

import numpy as np
import pytest

import pyobs.utils.exceptions as exc
from pyobs.images import Image, ImageProcessor
from pyobs.images.meta import DataPipelineName
from pyobs.interfaces import IDataPipeline
from pyobs.mixins.datapipeline import DataPipelineMixin
from pyobs.modules import Module
from pyobs.modules.camera import DummyCamera
from pyobs.modules.camera.dummyvideo import DummyVideo

# frame_number=False (with a filename pattern that doesn't need FRAMENUM): the per-frame
# FRAMENUM default does a real VFS read+write, which is both irrelevant here and, under this
# environment's default VFS root, occasionally slow enough to make these tests flaky
_TEST_CAMERA_FILENAMES = "/cache/pyobs-{DAY-OBS|date:}-{DATE-OBS|time:}-{IMAGETYP|type}00.fits.gz"
_TEST_VIDEO_FILENAMES = "/webcam/pyobs-{DAY-OBS|date:}-{DATE-OBS|time:}.fits"


class DoubleStep(ImageProcessor):
    """Test processor: doubles the data, so tests can tell whether it ran."""

    async def __call__(self, image: Image) -> Image:
        image.data = image.data * 2
        return image


class TagStep(ImageProcessor):
    """Test processor: fails unless a given header is already present -- used to check a
    pipeline runs after a subclass's own _finish_image() headers."""

    def __init__(self, required_header: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.required_header = required_header

    async def __call__(self, image: Image) -> Image:
        if self.required_header not in image.header:
            raise exc.ImageError(f"{self.required_header} not set yet")
        image.header["TAGGED"] = True
        return image


class RaisingStep(ImageProcessor):
    async def __call__(self, image: Image) -> Image:
        raise exc.ImageError("boom")


class _PipelineHost(Module, DataPipelineMixin):
    """Minimal Module host for testing the mixin in isolation."""

    def __init__(self, **kwargs: Any):
        Module.__init__(self, **kwargs)

    async def open(self) -> None:
        await Module.open(self)
        await self._datapipeline_open()


def make_host(**kwargs: Any) -> _PipelineHost:
    host = _PipelineHost(**kwargs)
    host.comm.set_state = AsyncMock()
    host.comm.set_capabilities = AsyncMock()
    return host


def make_camera(**kwargs: Any) -> DummyCamera:
    camera = DummyCamera(readout_time=0, frame_number=False, filenames=_TEST_CAMERA_FILENAMES, **kwargs)
    camera.comm.set_state = AsyncMock()
    camera.comm.set_capabilities = AsyncMock()
    camera.vfs.write_image = AsyncMock()
    return camera


def make_video(**kwargs: Any) -> DummyVideo:
    video = DummyVideo(fps=1000, image_size=(4, 4), frame_number=False, filenames=_TEST_VIDEO_FILENAMES, **kwargs)
    video.comm.set_state = AsyncMock()
    video.comm.set_capabilities = AsyncMock()
    video.request_fits_headers = AsyncMock(return_value={})
    return video


# ── config validation ────────────────────────────────────────────────────────


def test_unknown_default_pipeline_raises() -> None:
    with pytest.raises(ValueError):
        make_host(pipelines={"a": []}, default_pipeline="b")


def test_default_pipeline_without_pipelines_raises() -> None:
    with pytest.raises(ValueError):
        make_host(default_pipeline="a")


def test_empty_pipeline_name_raises() -> None:
    with pytest.raises(ValueError):
        make_host(pipelines={"": []})


@pytest.mark.parametrize("name", ["none", "None", "NONE"])
def test_reserved_pipeline_name_raises(name: str) -> None:
    with pytest.raises(ValueError):
        make_host(pipelines={name: []})


def test_valid_config_ok() -> None:
    host = make_host(pipelines={"a": [], "b": []}, default_pipeline="a")
    assert host._data_pipeline == "a"


# ── set_pipeline / _datapipeline_open ───────────────────────────────────────


@pytest.mark.asyncio
async def test_set_pipeline_unknown_raises() -> None:
    host = make_host(pipelines={"a": []})
    await host.open()

    with pytest.raises(exc.InvalidArgumentError):
        await host.set_pipeline("unknown")


@pytest.mark.asyncio
async def test_set_pipeline_valid_name_publishes_state() -> None:
    host = make_host(pipelines={"a": []})
    await host.open()
    host.comm.set_state.reset_mock()

    await host.set_pipeline("a")

    assert host._data_pipeline == "a"
    host.comm.set_state.assert_awaited_once()
    interface, state = host.comm.set_state.await_args[0]
    assert interface is IDataPipeline
    assert state.pipeline == "a"


@pytest.mark.asyncio
async def test_set_pipeline_none_publishes_state() -> None:
    host = make_host(pipelines={"a": []}, default_pipeline="a")
    await host.open()
    host.comm.set_state.reset_mock()

    await host.set_pipeline(None)

    assert host._data_pipeline is None
    interface, state = host.comm.set_state.await_args[0]
    assert interface is IDataPipeline
    assert state.pipeline is None


@pytest.mark.asyncio
async def test_datapipeline_open_publishes_sorted_capabilities_and_initial_state() -> None:
    host = make_host(pipelines={"zeta": [], "alpha": []}, default_pipeline="zeta")

    await host.open()

    interface, caps = host.comm.set_capabilities.await_args[0]
    assert interface is IDataPipeline
    assert caps.pipelines == ["alpha", "zeta"]

    interface, state = host.comm.set_state.await_args[0]
    assert interface is IDataPipeline
    assert state.pipeline == "zeta"


# ── _run_data_pipeline ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_data_pipeline_none_leaves_image_unchanged() -> None:
    host = make_host()
    await host.open()

    image = Image(np.ones((2, 2)))
    result = await host._run_data_pipeline(image, None)

    np.testing.assert_array_equal(result.data, np.ones((2, 2)))
    assert result.header["PIPELINE"] == "none"


@pytest.mark.asyncio
async def test_run_data_pipeline_runs_named_pipeline() -> None:
    host = make_host(pipelines={"double": [DoubleStep()]})
    await host.open()

    image = Image(np.ones((2, 2)))
    result = await host._run_data_pipeline(image, "double")

    np.testing.assert_array_equal(result.data, np.full((2, 2), 2.0))
    assert result.header["PIPELINE"] == "double"


@pytest.mark.asyncio
async def test_run_data_pipeline_default_on_error_raises_grabimageerror() -> None:
    host = make_host(pipelines={"bad": [RaisingStep()]})
    await host.open()

    with pytest.raises(exc.GrabImageError):
        await host._run_data_pipeline(Image(np.ones((2, 2))), "bad")


@pytest.mark.asyncio
async def test_run_data_pipeline_on_error_info_passes_through() -> None:
    host = make_host(pipelines={"bad": [RaisingStep(on_error="info")]})
    await host.open()

    result = await host._run_data_pipeline(Image(np.ones((2, 2))), "bad")

    np.testing.assert_array_equal(result.data, np.ones((2, 2)))
    assert result.header["PIPELINE"] == "bad"


# ── BaseCamera integration ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dummycamera_grab_data_stores_processed_image_with_pipeline_header() -> None:
    camera = make_camera(pipelines={"double": [DoubleStep()]}, default_pipeline="double")
    await camera.open()

    filename = await camera.grab_data()

    assert filename is not None
    camera.vfs.write_image.assert_awaited_once()
    written_filename, written_image = camera.vfs.write_image.await_args[0]
    assert written_filename == filename
    assert written_image.header["PIPELINE"] == "double"


@pytest.mark.asyncio
async def test_dummycamera_grab_data_pipeline_failure_writes_nothing_and_goes_idle() -> None:
    camera = make_camera(pipelines={"bad": [RaisingStep()]}, default_pipeline="bad")
    await camera.open()

    with pytest.raises(exc.GrabImageError):
        await camera.grab_data()

    camera.vfs.write_image.assert_not_called()
    from pyobs.utils.enums import ExposureStatus

    assert camera._camera_status == ExposureStatus.IDLE


@pytest.mark.asyncio
async def test_dummycamera_pipeline_captured_at_grab_start() -> None:
    """Changing the pipeline while a grab is in flight must not affect that grab."""
    camera = make_camera(pipelines={"double": [DoubleStep()]})
    await camera.open()

    original_expose = camera._expose

    async def slow_expose(*args: Any, **kwargs: Any) -> Image:
        # switch pipelines mid-grab, after grab_data() already captured the old selection
        await camera.set_pipeline("double")
        return await original_expose(*args, **kwargs)

    camera._expose = slow_expose  # type: ignore[method-assign]

    filename = await camera.grab_data()

    written_image = camera.vfs.write_image.await_args[0][1]
    assert written_image.header["PIPELINE"] == "none"
    assert filename is not None


# ── BaseVideo integration ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dummyvideo_grab_data_returns_processed_image() -> None:
    video = make_video(pipelines={"double": [DoubleStep()]}, default_pipeline="double")

    task = asyncio.create_task(video.grab_data())
    await asyncio.sleep(0.02)
    await video._set_image(np.ones((4, 4), dtype=np.uint16))
    await asyncio.sleep(0.02)
    await video._set_image(np.full((4, 4), 3, dtype=np.uint16))

    filename = await asyncio.wait_for(task, timeout=2)
    assert os.path.basename(filename) in video._cache


@pytest.mark.asyncio
async def test_dummyvideo_pipeline_runs_after_finish_image_override_headers() -> None:
    class _HeaderTaggingVideo(DummyVideo):
        async def _finish_image(self, image: Image, broadcast: bool, image_type: Any) -> tuple[Image, str]:
            image.header["CUSTOM"] = True
            return await super()._finish_image(image, broadcast, image_type)

    video = _HeaderTaggingVideo(
        fps=1000, image_size=(4, 4), pipelines={"tag": [TagStep("CUSTOM")]}, default_pipeline="tag"
    )
    video.comm.set_state = AsyncMock()
    video.comm.set_capabilities = AsyncMock()
    video.request_fits_headers = AsyncMock(return_value={})

    task = asyncio.create_task(video.grab_data())
    await asyncio.sleep(0.02)
    await video._set_image(np.ones((4, 4), dtype=np.uint16))
    await asyncio.sleep(0.02)
    await video._set_image(np.ones((4, 4), dtype=np.uint16))

    await asyncio.wait_for(task, timeout=2)


@pytest.mark.asyncio
async def test_dummyvideo_meta_fallback_when_create_image_bypasses_base() -> None:
    """A subclass replacing _create_image() without calling the base (like GregoryCamera) must
    still get the currently selected pipeline via the meta-missing fallback."""

    class _BypassingVideo(DummyVideo):
        async def _create_image(self, data: np.ndarray, next_image: Any) -> tuple[Image, str]:
            image = Image(data)
            image.header["DATE-OBS"] = next_image.date_obs
            image.header["IMAGETYP"] = next_image.image_type
            await self.add_fits_headers(image)
            return await self._finish_image(image, next_image.broadcast, next_image.image_type)

    video = _BypassingVideo(
        fps=1000, image_size=(4, 4), pipelines={"double": [DoubleStep()]}, default_pipeline="double"
    )
    video.comm.set_state = AsyncMock()
    video.comm.set_capabilities = AsyncMock()
    video.request_fits_headers = AsyncMock(return_value={})

    task = asyncio.create_task(video.grab_data())
    await asyncio.sleep(0.02)
    await video._set_image(np.ones((4, 4), dtype=np.uint16))
    await asyncio.sleep(0.02)
    await video._set_image(np.ones((4, 4), dtype=np.uint16))

    filename = await asyncio.wait_for(task, timeout=2)
    data = video._cache[os.path.basename(filename)]
    image = Image.from_bytes(data)
    assert image.header["PIPELINE"] == "double"


@pytest.mark.asyncio
async def test_dummyvideo_explicit_none_meta_overrides_fallback() -> None:
    """An image with DataPipelineName(None) meta gets no pipeline even when one is selected --
    only a *missing* meta falls back to the currently selected pipeline."""
    video = make_video(pipelines={"double": [DoubleStep()]}, default_pipeline="double")

    def fake_format_filename(image: Image) -> str:
        image.header["FNAME"] = "test.fits"
        return "test.fits"

    video.format_filename = fake_format_filename  # type: ignore[method-assign]

    image = Image(np.ones((4, 4)))
    image.set_meta(DataPipelineName(None))

    result_image, _ = await video._finish_image(image, broadcast=False, image_type=video._image_type)

    assert result_image.header["PIPELINE"] == "none"
    np.testing.assert_array_equal(result_image.data, np.ones((4, 4)))


@pytest.mark.asyncio
async def test_dummyvideo_reset_restores_default_pipeline() -> None:
    video = make_video(pipelines={"a": [], "b": []}, default_pipeline="a")
    await video.set_pipeline("b")

    await video.reset()

    assert video._data_pipeline == "a"


@pytest.mark.asyncio
async def test_dummycamera_reset_restores_default_pipeline() -> None:
    camera = make_camera(pipelines={"a": [], "b": []}, default_pipeline="a")
    await camera.set_pipeline("b")

    await camera.reset()

    assert camera._data_pipeline == "a"
