from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import Angle

import pyobs.utils.exceptions as exc
from pyobs.comm import Comm
from pyobs.images import Image
from pyobs.images.meta import OnSkyDistance
from pyobs.images.meta.exptime import ExpTime
from pyobs.interfaces import (
    AltAzOffsetState,
    AltAzState,
    IAcquisition,
    IOffsetsAltAz,
    IOffsetsRaDec,
    IPointingAltAz,
    IPointingRaDec,
    IRunning,
    RaDecOffsetState,
    RaDecState,
)
from pyobs.modules.pointing.acquisition import Acquisition
from pyobs.utils.enums import OffsetFrame
from pyobs.utils.offsets import ApplyOffsets
from pyobs.utils.offsets.applyoffsets import OffsetResult
from tests.helpers import make_proxy_cm


def make_acquisition(apply=None, **kwargs) -> Acquisition:
    comm = MagicMock(spec=Comm)
    if apply is None:
        apply = AsyncMock(spec=ApplyOffsets)
        apply.return_value = OffsetResult(applied=False)
    return Acquisition(
        camera="camera",
        telescope="telescope",
        pipeline=kwargs.pop("pipeline", []),
        apply=apply,
        exposure_time=1.0,
        comm=comm,
        **kwargs,
    )


def make_image(distance_arcsec: float | None = 5.0) -> Image:
    image = Image(data=np.zeros((4, 4)))
    if distance_arcsec is not None:
        image.set_meta(OnSkyDistance(distance=Angle(distance_arcsec * u.arcsec)))
    return image


def wire_comm(acq: Acquisition, camera: MagicMock, telescope: MagicMock) -> None:
    def proxy_se(name: object, iface: object = None) -> MagicMock:
        return make_proxy_cm(camera if name == "camera" else telescope)

    acq._comm.proxy = MagicMock(side_effect=proxy_se)
    acq._comm.safe_proxy = MagicMock(side_effect=proxy_se)


def make_camera(filename: str | None = "img.fits") -> MagicMock:
    camera = MagicMock()
    camera.set_exposure_time = AsyncMock()
    camera.set_image_type = AsyncMock()
    camera.grab_data = AsyncMock(return_value=filename)
    return camera


def make_telescope(offsets_frame: str | None = None) -> MagicMock:
    """offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets interface)."""
    telescope = MagicMock()

    def get_state_se(iface: object) -> object:
        if iface is IOffsetsRaDec and offsets_frame == "radec":
            return RaDecOffsetState(ra=1.0, dec=2.0)
        if iface is IOffsetsAltAz and offsets_frame == "altaz":
            return AltAzOffsetState(alt=3.0, az=4.0)
        if iface is IPointingAltAz:
            return AltAzState(alt=45.0, az=90.0)
        if iface is IPointingRaDec:
            return RaDecState(ra=10.0, dec=20.0)
        return None

    telescope.get_state = MagicMock(side_effect=get_state_se)
    return telescope


def _state_for(mock: AsyncMock, interface: object) -> object:
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    acq = make_acquisition()
    assert acq._is_running is False
    assert acq._attempts == 5
    assert acq._oneshot is False
    assert acq._attempts_log == []


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_initial_states(mocker) -> None:
    from pyobs.modules import Module

    acq = make_acquisition()
    acq._comm.has_proxy = AsyncMock(return_value=True)
    acq._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await acq.open()

    running_state = _state_for(acq._comm.set_state, IRunning)
    assert running_state.running is False
    _state_for(acq._comm.set_state, IAcquisition)  # just needs to exist


@pytest.mark.asyncio
async def test_is_running_reflects_flag() -> None:
    acq = make_acquisition()
    assert await acq.is_running() is False
    acq._is_running = True
    assert await acq.is_running() is True


# ── acquire_target ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acquire_target_toggles_running_flag() -> None:
    acq = make_acquisition()
    acq._comm.set_state = AsyncMock()
    acq._acquire = AsyncMock(return_value="result")

    result = await acq.acquire_target()

    assert result == "result"
    assert acq._is_running is False
    states = [c.args[1].running for c in acq._comm.set_state.await_args_list if c.args[0] is IRunning]
    assert states == [True, False]


@pytest.mark.asyncio
async def test_acquire_target_resets_running_flag_on_exception() -> None:
    acq = make_acquisition()
    acq._comm.set_state = AsyncMock()
    acq._acquire = AsyncMock(side_effect=exc.AcquisitionError("nope"))

    with pytest.raises(exc.AcquisitionError):
        await acq.acquire_target()

    assert acq._is_running is False


# ── _acquire ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acquire_raises_when_aborted_before_first_attempt() -> None:
    acq = make_acquisition()
    camera = make_camera()
    telescope = make_telescope()
    wire_comm(acq, camera, telescope)
    acq._abort_event.set()

    with pytest.raises(exc.AbortedError):
        await acq._acquire(1.0)


@pytest.mark.asyncio
async def test_acquire_succeeds_within_tolerance() -> None:
    acq = make_acquisition(tolerance=10.0)
    camera = make_camera()
    telescope = make_telescope("radec")
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image(distance_arcsec=1.0))
    acq._comm.set_state = AsyncMock()

    result = await acq._acquire(1.0)

    assert result.ra == 10.0
    assert result.offset_frame == OffsetFrame.RA_DEC
    assert len(acq._attempts_log) == 1
    assert bool(acq._attempts_log[0].offset_applied) is False  # within tolerance, no offset needed


@pytest.mark.asyncio
async def test_acquire_raises_when_offset_too_large() -> None:
    acq = make_acquisition(tolerance=1.0, max_offset=10.0)
    camera = make_camera()
    telescope = make_telescope()
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image(distance_arcsec=100.0))
    acq._comm.set_state = AsyncMock()

    with pytest.raises(exc.ImageError):
        await acq._acquire(1.0)


@pytest.mark.asyncio
async def test_acquire_applies_offset_and_continues() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=True, frame=OffsetFrame.RA_DEC, lon=1.0, lat=2.0)
    acq = make_acquisition(apply=apply, tolerance=1.0, max_offset=100.0, attempts=2)
    camera = make_camera()
    telescope = make_telescope("radec")
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    # first attempt: outside tolerance (10"), second: within tolerance (0.5")
    images = [make_image(distance_arcsec=10.0), make_image(distance_arcsec=0.5)]
    acq._vfs.read_image = AsyncMock(side_effect=images)
    acq._comm.set_state = AsyncMock()

    result = await acq._acquire(1.0)

    assert apply.await_count == 1  # only called for the attempt outside tolerance
    assert len(acq._attempts_log) == 2
    assert bool(acq._attempts_log[0].offset_applied) is True
    assert acq._attempts_log[0].offset_frame == OffsetFrame.RA_DEC
    assert bool(acq._attempts_log[1].offset_applied) is False
    assert result is not None


@pytest.mark.asyncio
async def test_acquire_finishes_after_oneshot_regardless_of_tolerance() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=True, frame=OffsetFrame.RA_DEC, lon=1.0, lat=2.0)
    acq = make_acquisition(apply=apply, tolerance=1.0, max_offset=100.0, oneshot=True)
    camera = make_camera()
    telescope = make_telescope("radec")
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image(distance_arcsec=10.0))  # outside tolerance
    acq._comm.set_state = AsyncMock()

    result = await acq._acquire(1.0)

    assert result is not None
    assert len(acq._attempts_log) == 1


@pytest.mark.asyncio
async def test_acquire_raises_after_exhausting_attempts() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=True, frame=OffsetFrame.RA_DEC, lon=1.0, lat=2.0)
    acq = make_acquisition(apply=apply, tolerance=1.0, max_offset=100.0, attempts=3)
    camera = make_camera()
    telescope = make_telescope("radec")
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image(distance_arcsec=10.0))  # always outside tolerance
    acq._comm.set_state = AsyncMock()

    with pytest.raises(exc.AcquisitionError):
        await acq._acquire(1.0)

    assert len(acq._attempts_log) == 3


@pytest.mark.asyncio
async def test_acquire_skips_attempt_when_filename_is_none() -> None:
    acq = make_acquisition(attempts=1)
    camera = make_camera(filename=None)
    telescope = make_telescope()
    wire_comm(acq, camera, telescope)
    acq._comm.set_state = AsyncMock()

    with pytest.raises(exc.AcquisitionError):
        await acq._acquire(1.0)

    assert acq._attempts_log == []  # never got far enough to log an attempt


@pytest.mark.asyncio
async def test_acquire_skips_attempt_on_pipeline_error() -> None:
    acq = make_acquisition(attempts=1)
    acq.run_pipeline = AsyncMock(side_effect=RuntimeError("bad pipeline"))
    camera = make_camera()
    telescope = make_telescope()
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image())
    acq._comm.set_state = AsyncMock()

    with pytest.raises(exc.AcquisitionError):
        await acq._acquire(1.0)


@pytest.mark.asyncio
async def test_acquire_skips_attempt_without_onskydistance_meta() -> None:
    acq = make_acquisition(attempts=1)
    camera = make_camera()
    telescope = make_telescope()
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()
    acq._vfs.read_image = AsyncMock(return_value=make_image(distance_arcsec=None))
    acq._comm.set_state = AsyncMock()

    with pytest.raises(exc.AcquisitionError):
        await acq._acquire(1.0)


@pytest.mark.asyncio
async def test_acquire_updates_exposure_time_from_meta() -> None:
    apply = AsyncMock(spec=ApplyOffsets)
    apply.return_value = OffsetResult(applied=True, frame=OffsetFrame.RA_DEC, lon=1.0, lat=2.0)
    acq = make_acquisition(apply=apply, tolerance=1.0, max_offset=100.0, attempts=2)
    camera = make_camera()
    telescope = make_telescope("radec")
    wire_comm(acq, camera, telescope)
    acq._vfs = MagicMock()

    image_with_exptime = make_image(distance_arcsec=10.0)
    image_with_exptime.set_meta(ExpTime(exptime=3.0))
    acq._vfs.read_image = AsyncMock(side_effect=[image_with_exptime, make_image(distance_arcsec=0.5)])
    acq._comm.set_state = AsyncMock()

    await acq._acquire(1.0)

    # second attempt should have used the updated exposure time
    assert camera.set_exposure_time.await_args_list[1].args[0] == 3.0


# ── _get_offsets ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_offsets_prefers_radec() -> None:
    acq = make_acquisition()
    telescope = make_telescope("radec")
    acq._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))

    frame, lon, lat = await acq._get_offsets()

    assert (frame, lon, lat) == (OffsetFrame.RA_DEC, 1.0, 2.0)


@pytest.mark.asyncio
async def test_get_offsets_falls_back_to_altaz() -> None:
    acq = make_acquisition()
    telescope = make_telescope("altaz")
    acq._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))

    frame, lon, lat = await acq._get_offsets()

    assert (frame, lon, lat) == (OffsetFrame.ALT_AZ, 3.0, 4.0)


@pytest.mark.asyncio
async def test_get_offsets_returns_none_when_unsupported() -> None:
    acq = make_acquisition()
    telescope = make_telescope(None)
    acq._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))

    frame, lon, lat = await acq._get_offsets()

    assert (frame, lon, lat) == (None, None, None)


# ── _create_log_and_return ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_log_and_return_builds_result() -> None:
    acq = make_acquisition()
    telescope = make_telescope("radec")
    wire_comm(acq, make_camera(), telescope)
    acq._comm.set_state = AsyncMock()

    result = await acq._create_log_and_return()

    assert result.alt == 45.0
    assert result.az == 90.0
    assert result.ra == 10.0
    assert result.dec == 20.0
    assert result.offset_frame == OffsetFrame.RA_DEC


@pytest.mark.asyncio
async def test_create_log_and_return_writes_to_publisher() -> None:
    publisher = AsyncMock()
    acq = make_acquisition()
    acq._publisher = publisher
    telescope = make_telescope("radec")
    wire_comm(acq, make_camera(), telescope)
    acq._comm.set_state = AsyncMock()

    await acq._create_log_and_return()

    publisher.assert_awaited_once()


# ── abort ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abort_sets_event() -> None:
    acq = make_acquisition()
    assert not acq._abort_event.is_set()
    await acq.abort()
    assert acq._abort_event.is_set()
