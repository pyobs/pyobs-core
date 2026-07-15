from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from pyobs.comm import Comm
from pyobs.images import Image
from pyobs.interfaces import (
    IAutoGuiding,
    IExposure,
    IExposureTime,
    IRunning,
)
from pyobs.modules.pointing.autoguiding import AutoGuiding
from pyobs.utils.enums import ExposureStatus, OffsetFrame
from pyobs.utils.offsets import ApplyOffsets
from pyobs.utils.offsets.applyoffsets import OffsetResult
from tests.helpers import make_proxy_cm


def make_guiding(pipeline=None, apply=None, **kwargs) -> AutoGuiding:
    comm = MagicMock(spec=Comm)
    if apply is None:
        apply = AsyncMock(spec=ApplyOffsets)
    return AutoGuiding(
        camera="camera",
        telescope="telescope",
        pipeline=[] if pipeline is None else pipeline,
        apply=apply,
        exposure_time=1.0,
        comm=comm,
        **kwargs,
    )


def make_image(
    imagetyp: str = "object",
    ra: float = 10.0,
    dec: float = 20.0,
    date_obs: str = "2024-01-01T00:00:00.000",
    filter_name: str = "clear",
    focus: float = 10.0,
    exptime: float = 1.0,
) -> Image:
    image = Image(data=np.zeros((4, 4)))
    image.header["IMAGETYP"] = imagetyp
    image.header["TEL-RA"] = ra
    image.header["TEL-DEC"] = dec
    image.header["DATE-OBS"] = date_obs
    image.header["FILTER"] = filter_name
    image.header["TEL-FOCU"] = focus
    image.header["EXPTIME"] = exptime
    return image


def _state_for(mock: AsyncMock, interface: object) -> object:
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    ag = make_guiding()
    assert ag._enabled is False
    assert ag._loop_closed is False
    from pyobs.modules.pointing.guidingstatistics import GuidingStatisticsPixelOffset

    assert isinstance(ag._statistics, GuidingStatisticsPixelOffset)


def test_init_with_custom_guiding_statistic() -> None:
    from pyobs.modules.pointing.guidingstatistics import GuidingStatisticsUptime

    stats = GuidingStatisticsUptime()
    ag = make_guiding(guiding_statistic=stats)
    assert ag._statistics is stats


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_initial_states(mocker) -> None:
    from pyobs.modules import Module

    ag = make_guiding()
    ag._comm.has_proxy = AsyncMock(return_value=True)
    ag._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await ag.open()

    running_state = _state_for(ag._comm.set_state, IRunning)
    assert running_state.running is False
    guiding_state = _state_for(ag._comm.set_state, IAutoGuiding)
    assert guiding_state.loop_closed is False


# ── start / stop / is_running ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_enables_guiding_and_sets_exposure_time() -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()

    await ag.start()

    assert ag._enabled is True
    assert ag._exposure_time == ag._default_exposure_time
    running_state = _state_for(ag._comm.set_state, IRunning)
    assert running_state.running is True


@pytest.mark.asyncio
async def test_stop_disables_guiding_and_waits_for_idle() -> None:
    ag = make_guiding()
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    camera = MagicMock(spec=IExposure)
    camera.get_state = MagicMock(return_value=None)  # no state -> loop exits immediately
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))

    await ag.stop()

    assert ag._enabled is False
    running_state = _state_for(ag._comm.set_state, IRunning)
    assert running_state.running is False


@pytest.mark.asyncio
async def test_stop_waits_until_camera_idle(mocker) -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()
    camera = MagicMock(spec=IExposure)
    states = [MagicMock(status=ExposureStatus.EXPOSING), MagicMock(status=ExposureStatus.IDLE)]
    camera.get_state = MagicMock(side_effect=states)
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))
    mocker.patch("pyobs.modules.pointing.autoguiding.asyncio.sleep", AsyncMock())

    await ag.stop()

    assert camera.get_state.call_count == 2


@pytest.mark.asyncio
async def test_is_running_reflects_enabled_flag() -> None:
    ag = make_guiding()
    assert await ag.is_running() is False
    ag._enabled = True
    assert await ag.is_running() is True


# ── set_exposure_time (AutoGuiding-specific) ────────────────────────────────


@pytest.mark.asyncio
async def test_set_exposure_time_updates_state_and_resets() -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()
    ag._loop_closed = True

    await ag.set_exposure_time(2.5)

    assert ag._default_exposure_time == 2.5
    assert ag._exposure_time is None
    assert ag._loop_closed is False
    state = _state_for(ag._comm.set_state, IExposureTime)
    assert state.exposure_time == 2.5


# ── get_fits_header_before / after ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_fits_header_before_reports_open_loop() -> None:
    ag = make_guiding()
    ag._statistics.init_stats = MagicMock()
    ag._uptime.init_stats = MagicMock()

    hdr = await ag.get_fits_header_before(sender="camera")

    assert hdr["AGSTATE"].value == "GUIDING_OPEN_LOOP"
    ag._statistics.init_stats.assert_called_once_with("camera")
    ag._uptime.init_stats.assert_called_once_with("camera", False)


@pytest.mark.asyncio
async def test_get_fits_header_before_reports_closed_loop() -> None:
    ag = make_guiding()
    ag._loop_closed = True
    ag._statistics.init_stats = MagicMock()
    ag._uptime.init_stats = MagicMock()

    hdr = await ag.get_fits_header_before(sender="camera")

    assert hdr["AGSTATE"].value == "GUIDING_CLOSED_LOOP"


@pytest.mark.asyncio
async def test_get_fits_header_after_includes_statistics() -> None:
    ag = make_guiding()
    ag._statistics.add_to_header = MagicMock(side_effect=lambda client, hdr: {**hdr, "STAT": "x"})
    ag._uptime.add_to_header = MagicMock(side_effect=lambda client, hdr: {**hdr, "UPTIME": "y"})

    hdr = await ag.get_fits_header_after(sender="camera")

    assert hdr["AGSTATE"].value == "GUIDING_OPEN_LOOP"
    assert hdr["STAT"] == "x"
    assert hdr["UPTIME"] == "y"


# ── _reset_guiding / _set_loop_state ────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_guiding_without_image_clears_headers() -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()
    ag._ref_header = {"OLD": 1}
    ag._last_header = {"OLD": 1}

    await ag._reset_guiding(enabled=True)

    assert ag._enabled is True
    assert ag._ref_header is None
    assert ag._last_header is None


@pytest.mark.asyncio
async def test_reset_guiding_with_image_sets_reference() -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()
    image = make_image()

    await ag._reset_guiding(enabled=True, image=image)

    assert ag._ref_header is image.header
    assert ag._last_header is image.header


@pytest.mark.asyncio
async def test_set_loop_state_publishes_offset_frame() -> None:
    ag = make_guiding()
    ag._comm.set_state = AsyncMock()

    await ag._set_loop_state(True, OffsetFrame.RA_DEC, 1.5, 2.5)

    assert ag._loop_closed is True
    assert ag._last_offset_frame == OffsetFrame.RA_DEC
    state = _state_for(ag._comm.set_state, IAutoGuiding)
    assert state.loop_closed is True
    assert state.offset_frame == OffsetFrame.RA_DEC
    assert state.offset_lon == 1.5
    assert state.offset_lat == 2.5


# ── _process_image ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_image_returns_none_when_disabled() -> None:
    ag = make_guiding()
    assert await ag._process_image(make_image()) is None


@pytest.mark.asyncio
async def test_process_image_returns_none_for_wrong_image_type() -> None:
    ag = make_guiding()
    ag._enabled = True
    assert await ag._process_image(make_image(imagetyp="bias")) is None


@pytest.mark.asyncio
async def test_process_image_sets_reference_on_first_image() -> None:
    ag = make_guiding()
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    image = make_image()

    result = await ag._process_image(image)

    assert result is None
    assert ag._ref_header is image.header


@pytest.mark.asyncio
async def test_process_image_resets_on_large_separation() -> None:
    ag = make_guiding(separation_reset=1.0)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(ra=10.0, dec=20.0)
    await ag._reset_guiding(enabled=True, image=ref)

    moved = make_image(ra=10.5, dec=20.5)  # well over 1 arcsec away
    result = await ag._process_image(moved)

    assert result is None
    assert ag._ref_header is moved.header  # reference reset to the new image


@pytest.mark.asyncio
async def test_process_image_resets_on_filter_change() -> None:
    ag = make_guiding()
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(filter_name="clear")
    await ag._reset_guiding(enabled=True, image=ref)

    changed = make_image(filter_name="red")
    result = await ag._process_image(changed)

    assert result is None
    assert ag._ref_header is changed.header


@pytest.mark.asyncio
async def test_process_image_resets_on_large_time_gap() -> None:
    ag = make_guiding(max_interval=10)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(date_obs="2024-01-01T00:00:00.000")
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header  # simulate a previous non-reference frame too

    later = make_image(date_obs="2024-01-01T00:05:00.000")  # 300s later
    result = await ag._process_image(later)

    assert result is None
    assert ag._ref_header is later.header


@pytest.mark.asyncio
async def test_process_image_ignores_image_too_soon() -> None:
    ag = make_guiding(min_interval=100)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(date_obs="2024-01-01T00:00:00.000")
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header

    soon = make_image(date_obs="2024-01-01T00:00:01.000")  # only 1s later
    result = await ag._process_image(soon)

    assert result is None
    assert ag._last_header is ref.header  # unchanged -- image was ignored


@pytest.mark.asyncio
async def test_process_image_resets_on_focus_change() -> None:
    ag = make_guiding()
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(focus=10.0)
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header

    refocused = make_image(focus=10.5)
    result = await ag._process_image(refocused)

    assert result is None
    assert ag._ref_header is refocused.header


@pytest.mark.asyncio
async def test_process_image_skips_when_exptime_too_large() -> None:
    ag = make_guiding(max_exposure_time=5.0)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ref = make_image(exptime=1.0)
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header

    long_exp = make_image(exptime=10.0)
    result = await ag._process_image(long_exp)

    assert result is None
    state = _state_for(ag._comm.set_state, IAutoGuiding)
    assert state.loop_closed is False


@pytest.mark.asyncio
async def test_process_image_applies_offsets_successfully() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=True, frame=OffsetFrame.RA_DEC, lon=1.0, lat=2.0)
    ag = make_guiding(apply=apply)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ag._comm.has_proxy = AsyncMock(return_value=True)
    ref = make_image()
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header

    telescope = MagicMock()
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(telescope))

    next_image = make_image()
    result = await ag._process_image(next_image)

    assert result is not None
    assert ag._loop_closed is True
    apply.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_image_handles_offset_not_applied() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=False)
    ag = make_guiding(apply=apply)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ag._comm.has_proxy = AsyncMock(return_value=True)
    ref = make_image()
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(MagicMock()))

    result = await ag._process_image(make_image())

    assert result is not None
    assert ag._loop_closed is False


@pytest.mark.asyncio
async def test_process_image_handles_apply_value_error() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.side_effect = ValueError("bad offset")
    ag = make_guiding(apply=apply)
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ag._comm.has_proxy = AsyncMock(return_value=True)
    ref = make_image()
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(MagicMock()))

    result = await ag._process_image(make_image())

    assert result is not None
    assert ag._loop_closed is False


@pytest.mark.asyncio
async def test_process_image_handles_missing_telescope_proxy() -> None:
    ag = make_guiding()
    ag._enabled = True
    ag._comm.set_state = AsyncMock()
    ag._comm.has_proxy = AsyncMock(return_value=False)
    ref = make_image()
    await ag._reset_guiding(enabled=True, image=ref)
    ag._last_header = ref.header

    result = await ag._process_image(make_image())

    assert result is not None
    assert ag._loop_closed is False


# ── _auto_guiding background loop ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_auto_guiding_sleeps_when_disabled(mocker) -> None:
    ag = make_guiding()

    async def fake_sleep(t: float) -> None:
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.pointing.autoguiding.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await ag._auto_guiding()


@pytest.mark.asyncio
async def test_auto_guiding_takes_and_processes_image_when_enabled(mocker) -> None:
    ag = make_guiding()
    ag._enabled = True

    camera = MagicMock()
    camera.grab_data = AsyncMock(return_value="filename.fits")
    ag._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))
    ag._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))

    image = make_image()
    ag._vfs = MagicMock()
    ag._vfs.read_image = AsyncMock(return_value=image)
    ag._process_image = AsyncMock(return_value=image)

    sleep_calls = 0

    async def fake_sleep(t: float) -> None:
        nonlocal sleep_calls
        sleep_calls += 1
        raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.pointing.autoguiding.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await ag._auto_guiding()

    camera.grab_data.assert_awaited_once()
    ag._process_image.assert_awaited_once_with(image)
    assert sleep_calls == 1
