from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IExposureTime
from pyobs.modules.camera.basevideo import BaseVideo
from pyobs.modules.camera.dummyvideo import DummyVideo


def make_dummyvideo(**kwargs) -> DummyVideo:
    comm = MagicMock(spec=Comm)
    return DummyVideo(comm=comm, **kwargs)


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    dv = make_dummyvideo()
    assert dv._fps == 1.0
    assert dv._image_size == (640, 480)
    assert dv._exposure_time == 1.0


def test_init_custom_fps_and_image_size() -> None:
    dv = make_dummyvideo(fps=4.0, image_size=(10, 20))
    assert dv._fps == 4.0
    assert dv._image_size == (10, 20)
    assert dv._exposure_time == 0.25


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_exposure_time_state(mocker) -> None:
    dv = make_dummyvideo(fps=2.0)
    dv._comm.set_state = AsyncMock()
    mocker.patch.object(BaseVideo, "open", AsyncMock())

    await dv.open()

    dv._comm.set_state.assert_awaited_once()
    interface, state = dv._comm.set_state.await_args[0]
    assert interface is IExposureTime
    assert state.exposure_time == 0.5


# ── set_exposure_time ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_exposure_time_updates_fps_and_publishes_state() -> None:
    dv = make_dummyvideo()
    dv._comm.set_state = AsyncMock()

    await dv.set_exposure_time(0.25)

    assert dv._exposure_time == 0.25
    assert dv._fps == 4.0
    dv._comm.set_state.assert_awaited_once()
    interface, state = dv._comm.set_state.await_args[0]
    assert interface is IExposureTime
    assert state.exposure_time == 0.25


@pytest.mark.asyncio
async def test_set_exposure_time_zero_falls_back_to_fps_one() -> None:
    dv = make_dummyvideo()
    dv._comm.set_state = AsyncMock()

    await dv.set_exposure_time(0.0)

    assert dv._exposure_time == 0.0
    assert dv._fps == 1.0


# ── _frame_task ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_frame_task_sets_image_when_active(mocker) -> None:
    dv = make_dummyvideo(image_size=(4, 3))
    dv._active = True
    dv._set_image = AsyncMock()

    async def fake_sleep(t: float) -> None:
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.camera.dummyvideo.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await dv._frame_task()

    dv._set_image.assert_awaited_once()
    data = dv._set_image.await_args[0][0]
    assert data.shape == (3, 4)  # (h, w)


@pytest.mark.asyncio
async def test_frame_task_skips_image_when_inactive(mocker) -> None:
    dv = make_dummyvideo()
    dv._active = False
    dv._set_image = AsyncMock()

    async def fake_sleep(t: float) -> None:
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.camera.dummyvideo.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await dv._frame_task()

    dv._set_image.assert_not_called()
