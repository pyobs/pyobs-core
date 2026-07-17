from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.interfaces import (
    ITrackingMode,
    ITrackingRate,
    TrackingMode,
    TrackingModeState,
    TrackingRateCapabilities,
)
from pyobs.modules.telescope.basetelescope import (
    _DEFAULT_REFRESH_INTERVAL_SECONDS,
    _MOON_FALLBACK_REFRESH_INTERVAL_SECONDS,
    BodyResolutionError,
)
from pyobs.modules.telescope.dummyradectelescope import DummyRaDecTelescope
from pyobs.utils import exceptions as exc


def make_dummyradectelescope(**kwargs) -> DummyRaDecTelescope:
    comm = MagicMock(spec=Comm)
    comm.get_own_state = MagicMock(return_value=None)
    comm.get_own_capabilities = MagicMock(return_value=None)
    comm.set_state = AsyncMock()
    comm.set_capabilities = AsyncMock()
    comm.send_event = AsyncMock()
    comm.register_event = AsyncMock()

    observer = kwargs.pop("observer", None)
    if observer is None:
        observer = Observer(latitude=52.0 * u.deg, longitude=10.0 * u.deg, elevation=100.0 * u.m)
    kwargs.setdefault("min_altitude", -90)
    kwargs.setdefault("location", observer.location)
    return DummyRaDecTelescope(comm=comm, observer=observer, **kwargs)


# ── set_tracking_mode ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_tracking_mode_valid_updates_state():
    tel = make_dummyradectelescope()
    await tel.set_tracking_mode(TrackingMode.LUNAR)
    assert tel._tracking_mode == TrackingMode.LUNAR
    interface, state = tel._comm.set_state.await_args.args
    assert interface is ITrackingMode
    assert state.mode == TrackingMode.LUNAR


@pytest.mark.asyncio
async def test_set_tracking_mode_invalid_raises_and_does_not_change_state():
    tel = make_dummyradectelescope()
    with pytest.raises(exc.InvalidArgumentError):
        await tel.set_tracking_mode("bogus")  # type: ignore[arg-type]
    assert tel._tracking_mode == TrackingMode.OFF


# ── open() publishes tracking capabilities/state ─────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_tracking_capabilities_and_state():
    tel = make_dummyradectelescope()
    await tel.open()
    interfaces_with_capabilities = {call.args[0] for call in tel._comm.set_capabilities.await_args_list}
    assert ITrackingMode in interfaces_with_capabilities
    assert ITrackingRate in interfaces_with_capabilities
    interfaces_with_state = {call.args[0] for call in tel._comm.set_state.await_args_list}
    assert ITrackingMode in interfaces_with_state
    assert ITrackingRate in interfaces_with_state


# ── move_radec / move_altaz side effects ─────────────────────────────────────


@pytest.mark.asyncio
async def test_move_radec_resets_tracking_mode_to_sidereal():
    tel = make_dummyradectelescope(speed=100000.0)  # near-instant sim slew
    await tel.open()  # _move_task (which drives the simulated slew) only starts after open()
    tel._tracking_mode = TrackingMode.LUNAR
    await tel.move_radec(10.0, 20.0)
    assert tel._tracking_mode == TrackingMode.SIDEREAL


@pytest.mark.asyncio
async def test_move_altaz_resets_tracking_mode_to_off():
    tel = make_dummyradectelescope(speed=100000.0)
    await tel.open()
    tel._tracking_mode = TrackingMode.LUNAR
    await tel.move_altaz(45.0, 90.0)
    assert tel._tracking_mode == TrackingMode.OFF


@pytest.mark.asyncio
async def test_move_radec_clears_tracked_body():
    tel = make_dummyradectelescope(speed=100000.0)
    await tel.open()
    tel._tracked_body = "mars"
    await tel.move_radec(10.0, 20.0)
    assert tel._tracked_body is None


@pytest.mark.asyncio
async def test_move_altaz_clears_tracked_body():
    tel = make_dummyradectelescope(speed=100000.0)
    await tel.open()
    tel._tracked_body = "mars"
    await tel.move_altaz(45.0, 90.0)
    assert tel._tracked_body is None


# ── set_tracking_rate SIDEREAL precondition ──────────────────────────────────


@pytest.mark.asyncio
async def test_set_tracking_rate_forces_sidereal_when_not_already():
    tel = make_dummyradectelescope()
    tel._tracking_mode = TrackingMode.LUNAR
    tel._comm.get_own_state = MagicMock(return_value=TrackingModeState(mode=TrackingMode.LUNAR))

    await tel.set_tracking_rate(1.0, -0.5)

    assert tel._tracking_mode == TrackingMode.SIDEREAL
    assert tel._tracking_rate == (1.0, -0.5)


@pytest.mark.asyncio
async def test_set_tracking_rate_skips_redundant_mode_switch_when_already_sidereal():
    tel = make_dummyradectelescope()
    tel._tracking_mode = TrackingMode.SIDEREAL
    tel._comm.get_own_state = MagicMock(return_value=TrackingModeState(mode=TrackingMode.SIDEREAL))
    tel.set_tracking_mode = AsyncMock(wraps=tel.set_tracking_mode)  # type: ignore[method-assign]

    await tel.set_tracking_rate(1.0, -0.5)

    tel.set_tracking_mode.assert_not_awaited()
    assert tel._tracking_rate == (1.0, -0.5)


# ── track_body ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_track_body_moon_slews_and_uses_native_lunar_mode():
    # astropy's builtin ephemeris resolves 'moon' with no network access needed
    tel = make_dummyradectelescope(speed=100000.0)
    await tel.open()
    await tel.track_body("moon")
    assert tel._tracked_body == "moon"
    assert tel._tracked_elements is None
    assert tel._tracking_mode == TrackingMode.LUNAR
    ra, dec = tel._position_radec
    assert 0.0 <= ra <= 360.0
    assert -90.0 <= dec <= 90.0


@pytest.mark.asyncio
async def test_track_body_unresolvable_raises_body_resolution_error():
    tel = make_dummyradectelescope(speed=100000.0)

    def _raise(*args, **kwargs):
        raise Exception("boom")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("pyobs.modules.telescope.basetelescope.Horizons", MagicMock(side_effect=_raise))
        with pytest.raises(BodyResolutionError):
            await tel.track_body("definitely-not-a-real-body-xyz")


# ── DummyRaDecTelescope's simulated tracking-rate motion ──────────────────────────


@pytest.mark.asyncio
async def test_move_task_applies_tracking_rate_to_position():
    tel = make_dummyradectelescope()
    await tel.open()  # _move_task only starts after open()
    ra0, dec0 = tel._position_radec
    tel._tracking_rate = (5.0, -2.0)  # arcsec/sec, exaggerated for a fast, reliable test

    await asyncio.sleep(1.2)  # let the 1s-cadence _move_task tick at least once

    ra1, dec1 = tel._position_radec
    assert ra1 != ra0
    assert dec1 != dec0
    # dec should have decreased, given a negative dec_rate
    assert dec1 < dec0


# ── _tracking_refresh_interval clamping against min_update_interval ──────────


def test_tracking_refresh_interval_defaults_when_no_capabilities_published():
    tel = make_dummyradectelescope()
    assert tel._tracking_refresh_interval() == _DEFAULT_REFRESH_INTERVAL_SECONDS


def test_tracking_refresh_interval_clamped_up_by_min_update_interval():
    tel = make_dummyradectelescope()
    tel._comm.get_own_capabilities = MagicMock(return_value=TrackingRateCapabilities(min_update_interval=900.0))
    assert tel._tracking_refresh_interval() == 900.0


def test_tracking_refresh_interval_not_clamped_down_below_accuracy_driven_default():
    tel = make_dummyradectelescope()
    tel._comm.get_own_capabilities = MagicMock(return_value=TrackingRateCapabilities(min_update_interval=10.0))
    assert tel._tracking_refresh_interval() == _DEFAULT_REFRESH_INTERVAL_SECONDS


def test_tracking_refresh_interval_moon_fallback_clamped_up():
    tel = make_dummyradectelescope()
    tel._tracked_body = "moon"
    tel._last_tracking_used_native_mode = False  # no native LUNAR available -> 60s fallback cadence
    tel._comm.get_own_capabilities = MagicMock(return_value=TrackingRateCapabilities(min_update_interval=120.0))
    assert tel._tracking_refresh_interval() == 120.0


def test_tracking_refresh_interval_moon_fallback_not_clamped_below_60s():
    tel = make_dummyradectelescope()
    tel._tracked_body = "moon"
    tel._last_tracking_used_native_mode = False
    tel._comm.get_own_capabilities = MagicMock(return_value=TrackingRateCapabilities(min_update_interval=5.0))
    assert tel._tracking_refresh_interval() == _MOON_FALLBACK_REFRESH_INTERVAL_SECONDS


def test_tracking_refresh_interval_warns_once_when_hardware_floor_degrades_tracking(caplog):
    tel = make_dummyradectelescope()
    tel._comm.get_own_capabilities = MagicMock(return_value=TrackingRateCapabilities(min_update_interval=900.0))

    with caplog.at_level("WARNING"):
        tel._tracking_refresh_interval()
        tel._tracking_refresh_interval()

    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
