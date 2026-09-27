"""Tests for IResettable: BaseCamera/BaseSpectrograph reset()/full_reset(), the DummyCamera
overrides, and Module.startup()'s automatic full_reset() call plus its gap warnings.

See specs/design/iresettable.md.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pyobs.interfaces import Binning, BinningCapabilities, IResettable, WindowCapabilities
from pyobs.modules import Module
from pyobs.modules.camera import DummyCamera, DummySpectrograph
from pyobs.modules.camera.basecamera import BaseCamera
from pyobs.modules.camera.dummycamera import CoolingStatus
from pyobs.modules.camera.dummyvideo import DummyVideo
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ExposureStatus, ImageFormat, ImageType


def make_camera() -> DummyCamera:
    camera = DummyCamera(readout_time=0)
    camera.comm.set_state = AsyncMock()
    return camera


def make_spectrograph() -> DummySpectrograph:
    spectrograph = DummySpectrograph()
    spectrograph.comm.set_state = AsyncMock()
    return spectrograph


# ── BaseCamera.reset() ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_restores_exposure_time_and_image_type() -> None:
    camera = make_camera()
    await camera.set_exposure_time(12.0)
    await camera.set_image_type(ImageType.DARK)

    await camera.reset()

    assert camera._exposure_time == 0.0
    assert camera._image_type == ImageType.OBJECT


@pytest.mark.asyncio
async def test_reset_sets_binning_and_window_full_frame_binning_first(mocker) -> None:
    camera = make_camera()
    order: list[str] = []

    def get_own_capabilities(iface):
        from pyobs.interfaces import IBinning, IWindow

        if iface is IBinning:
            return BinningCapabilities(binnings=[Binning(1, 1), Binning(2, 2)])
        if iface is IWindow:
            return WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=1024, full_frame_height=1024)
        return None

    mocker.patch.object(camera.comm, "get_own_capabilities", side_effect=get_own_capabilities)

    orig_set_binning = camera.set_binning
    orig_set_window = camera.set_window

    async def tracked_set_binning(*args, **kwargs):
        order.append("set_binning")
        return await orig_set_binning(*args, **kwargs)

    async def tracked_set_window(*args, **kwargs):
        order.append("set_window")
        return await orig_set_window(*args, **kwargs)

    mocker.patch.object(camera, "set_binning", side_effect=tracked_set_binning)
    mocker.patch.object(camera, "set_window", side_effect=tracked_set_window)

    await camera.reset()

    assert order == ["set_binning", "set_window"]
    assert camera._binning == (1, 1)
    assert camera._window == (0, 0, 1024, 1024)


@pytest.mark.asyncio
async def test_reset_skips_window_when_capabilities_none(mocker) -> None:
    camera = make_camera()
    mocker.patch.object(camera.comm, "get_own_capabilities", return_value=None)
    set_window = mocker.patch.object(camera, "set_window", wraps=camera.set_window)

    await camera.reset()

    set_window.assert_not_called()


@pytest.mark.asyncio
async def test_reset_skips_binning_when_1x1_not_in_capabilities(mocker) -> None:
    camera = make_camera()

    def get_own_capabilities(iface):
        from pyobs.interfaces import IBinning

        if iface is IBinning:
            return BinningCapabilities(binnings=[Binning(2, 2), Binning(3, 3)])
        return None

    mocker.patch.object(camera.comm, "get_own_capabilities", side_effect=get_own_capabilities)
    set_binning = mocker.patch.object(camera, "set_binning", wraps=camera.set_binning)

    await camera.reset()

    set_binning.assert_not_called()


@pytest.mark.asyncio
async def test_reset_raises_when_exposing() -> None:
    camera = make_camera()
    camera._camera_status = ExposureStatus.EXPOSING

    with pytest.raises(exc.DeviceBusyError):
        await camera.reset()


@pytest.mark.asyncio
async def test_reset_raises_when_sequence_running() -> None:
    camera = make_camera()
    camera._sequence_count_left = 3

    with pytest.raises(exc.DeviceBusyError):
        await camera.reset()


@pytest.mark.asyncio
async def test_reset_does_not_touch_cooling() -> None:
    camera = make_camera()
    await camera.set_cooling(True, -30.0)

    await camera.reset()

    assert camera._cooling.set_point == -30.0


# ── DummyCamera.full_reset() ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dummycamera_full_reset_restores_per_acquisition_settings_and_cooling() -> None:
    camera = make_camera()
    await camera.set_exposure_time(5.0)
    await camera.set_image_type(ImageType.DARK)
    await camera.set_gain(20.0)
    await camera.set_offset(5.0)
    await camera.set_image_format(ImageFormat.INT8)
    await camera.set_cooling(False, -30.0)

    await camera.full_reset()

    assert camera._exposure_time == 0.0
    assert camera._image_type == ImageType.OBJECT
    assert camera._gain == 10.0
    assert camera._gain_offset == 0.0
    assert camera._image_format == ImageFormat.INT16
    assert camera._cooling.enabled is True
    assert camera._cooling.set_point == CoolingStatus().set_point


@pytest.mark.asyncio
async def test_dummycamera_full_reset_raises_when_busy() -> None:
    camera = make_camera()
    camera._camera_status = ExposureStatus.EXPOSING

    with pytest.raises(exc.DeviceBusyError):
        await camera.full_reset()


@pytest.mark.asyncio
async def test_dummycamera_reset_resets_gain_offset_and_image_format() -> None:
    """Without DummyCamera's own reset() override, it would trigger the IGain/IImageFormat
    startup warning -- see test_startup_warns_about_unmigrated_gain below."""
    camera = make_camera()
    await camera.set_gain(42.0)

    await camera.reset()

    assert camera._gain == 10.0


# ── full_reset() falling back to reset() on classes without an override ────


@pytest.mark.asyncio
async def test_full_reset_without_override_behaves_like_reset() -> None:
    spectrograph = make_spectrograph()

    # no exception, same busy semantics as reset()
    await spectrograph.full_reset()

    spectrograph._spectrograph_status = ExposureStatus.EXPOSING
    with pytest.raises(exc.DeviceBusyError):
        await spectrograph.full_reset()


@pytest.mark.asyncio
async def test_dummyvideo_full_reset_without_override_behaves_like_reset() -> None:
    video = DummyVideo()
    video.comm.set_state = AsyncMock()
    await video.set_image_type(ImageType.DARK)

    await video.full_reset()

    assert video._image_type == ImageType.OBJECT


# ── BaseSpectrograph.reset() ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_spectrograph_reset_idle_ok() -> None:
    spectrograph = make_spectrograph()
    await spectrograph.reset()  # must not raise


@pytest.mark.asyncio
async def test_spectrograph_reset_busy_raises() -> None:
    spectrograph = make_spectrograph()
    spectrograph._spectrograph_status = ExposureStatus.EXPOSING

    with pytest.raises(exc.DeviceBusyError):
        await spectrograph.reset()


# ── Module.startup() calls full_reset() ─────────────────────────────────────


class _ResettableModule(Module, IResettable):
    def __init__(self, fail: bool = False, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self.reset_calls = 0
        self.full_reset_calls = 0
        self._fail = fail

    async def reset(self, **kwargs: Any) -> None:
        self.reset_calls += 1

    async def full_reset(self, **kwargs: Any) -> None:
        self.full_reset_calls += 1
        if self._fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_startup_calls_full_reset_not_reset() -> None:
    module = _ResettableModule(own_comm=False)

    await module.startup()

    assert module.full_reset_calls == 1
    assert module.reset_calls == 0


@pytest.mark.asyncio
async def test_startup_reaches_ready_when_full_reset_raises(caplog) -> None:
    module = _ResettableModule(fail=True, own_comm=False)

    with caplog.at_level(logging.ERROR):
        await module.startup()

    assert module.full_reset_calls == 1
    from pyobs.utils.enums import ModuleState

    assert module._state == ModuleState.READY
    assert any("Could not reset module" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_startup_module_without_iresettable_unaffected() -> None:
    class _PlainModule(Module):
        pass

    module = _PlainModule(own_comm=False)
    await module.startup()

    from pyobs.utils.enums import ModuleState

    assert module._state == ModuleState.READY


# ── Startup gap warnings ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_startup_warns_about_unmigrated_cooling(caplog) -> None:
    """A BaseCamera subclass implementing ICooling but not overriding full_reset() must warn
    on every startup, so the gap can't go stale."""
    from pyobs.interfaces import CoolingState, ICooling

    class _CoolingCamera(BaseCamera, ICooling):
        async def _expose(self, exposure_time, open_shutter, abort_event):
            raise NotImplementedError

        async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
            pass

        async def open(self) -> None:
            await BaseCamera.open(self)
            await self.comm.set_state(ICooling, CoolingState(setpoint=0.0, power=0, enabled=True))

    module = _CoolingCamera(own_comm=False)

    with caplog.at_level(logging.WARNING):
        await module.startup()

    assert any("doesn't override full_reset()" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_startup_dummycamera_logs_no_gap_warnings(caplog) -> None:
    camera = DummyCamera(own_comm=False)

    with caplog.at_level(logging.WARNING):
        await camera.startup()

    assert not any("doesn't override full_reset()" in r.message for r in caplog.records)
    assert not any("doesn't override reset()" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_startup_warns_about_unmigrated_gain(caplog) -> None:
    """A subclass overriding reset() but implementing IGain must still warn -- the marker check
    is on the actually-resolved reset(), not on whether *a* reset() override exists at all."""
    from pyobs.interfaces import GainState, IGain

    class _GainCamera(BaseCamera, IGain):
        async def _expose(self, exposure_time, open_shutter, abort_event):
            raise NotImplementedError

        async def set_gain(self, gain: float, **kwargs: Any) -> None:
            pass

        async def set_offset(self, offset: float, **kwargs: Any) -> None:
            pass

        async def open(self) -> None:
            await BaseCamera.open(self)
            await self.comm.set_state(IGain, GainState(gain=0.0, offset=0.0))

    module = _GainCamera(own_comm=False)

    with caplog.at_level(logging.WARNING):
        await module.startup()

    assert any("doesn't override reset()" in r.message and "IGain" in r.message for r in caplog.records)
