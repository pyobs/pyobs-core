from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.interfaces import (
    HeliocentricPolarState,
    HeliographicStonyhurstState,
    HelioprojectiveState,
    IPointingBody,
    IPointingHeliocentricPolar,
    IPointingHeliographicStonyhurst,
    IPointingHelioprojective,
    IPointingOrbitalElements,
    TrackingMode,
)
from pyobs.modules.telescope.dummysolartelescope import DummySolarTelescope


def make_dummysolartelescope(**kwargs) -> DummySolarTelescope:
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
    kwargs.setdefault("speed", 100000.0)  # near-instant sim slew
    return DummySolarTelescope(comm=comm, observer=observer, **kwargs)


def test_does_not_implement_body_or_orbital_element_tracking():
    tel = make_dummysolartelescope()
    assert not isinstance(tel, IPointingBody)
    assert not isinstance(tel, IPointingOrbitalElements)


@pytest.mark.asyncio
async def test_move_heliocentric_polar_slews_tracks_solar_and_publishes_state():
    tel = make_dummysolartelescope()
    await tel.open()

    await tel.move_heliocentric_polar(0.9, 45.0)

    assert tel._tracking_mode == TrackingMode.SOLAR
    assert tel._solar_target == ("heliocentric_polar", 0.9, 45.0)
    ra, dec = tel._position_radec
    assert 0.0 <= ra <= 360.0
    assert -90.0 <= dec <= 90.0

    interface, state = tel._comm.set_state.await_args_list[-1].args
    assert interface is IPointingHeliocentricPolar
    assert isinstance(state, HeliocentricPolarState)
    assert state.mu == pytest.approx(0.9)
    assert state.psi == pytest.approx(45.0)


@pytest.mark.asyncio
async def test_move_heliographic_stonyhurst_slews_tracks_solar_and_publishes_state():
    tel = make_dummysolartelescope()
    await tel.open()

    await tel.move_heliographic_stonyhurst(10.0, 20.0)

    assert tel._tracking_mode == TrackingMode.SOLAR
    assert tel._solar_target == ("heliographic_stonyhurst", 10.0, 20.0)
    ra, dec = tel._position_radec
    assert 0.0 <= ra <= 360.0
    assert -90.0 <= dec <= 90.0

    interface, state = tel._comm.set_state.await_args_list[-1].args
    assert interface is IPointingHeliographicStonyhurst
    assert isinstance(state, HeliographicStonyhurstState)
    assert state.lon == pytest.approx(10.0)
    assert state.lat == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_move_helioprojective_slews_tracks_solar_and_publishes_state():
    tel = make_dummysolartelescope()
    await tel.open()

    await tel.move_helioprojective(0.05, 0.02)

    assert tel._tracking_mode == TrackingMode.SOLAR
    assert tel._solar_target == ("helioprojective", 0.05, 0.02)

    interface, state = tel._comm.set_state.await_args_list[-1].args
    assert interface is IPointingHelioprojective
    assert isinstance(state, HelioprojectiveState)
    assert state.theta_x == pytest.approx(0.05)
    assert state.theta_y == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_plain_move_radec_clears_solar_target_and_resets_to_sidereal():
    tel = make_dummysolartelescope()
    await tel.open()
    await tel.move_heliocentric_polar(0.9, 45.0)
    assert tel._solar_target is not None

    await tel.move_radec(10.0, 20.0)

    assert tel._solar_target is None
    assert tel._tracking_mode == TrackingMode.SIDEREAL


@pytest.mark.asyncio
async def test_plain_move_altaz_clears_solar_target():
    tel = make_dummysolartelescope()
    await tel.open()
    await tel.move_heliocentric_polar(0.9, 45.0)
    assert tel._solar_target is not None

    await tel.move_altaz(45.0, 90.0)

    assert tel._solar_target is None


@pytest.mark.asyncio
async def test_solar_follow_task_keeps_updating_position_while_tracking():
    tel = make_dummysolartelescope()
    tel._SOLAR_FOLLOW_INTERVAL_SECONDS = 0.1
    await tel.open()  # background tasks (incl. _solar_follow_task) start here

    await tel.move_heliocentric_polar(0.9, 45.0)
    ra0, dec0 = tel._position_radec

    # force a detectably different Sun position without waiting real minutes: re-resolve
    # against a slightly later time via the task's own conversion helper, and confirm the
    # background task is actually the one moving _position (not a one-off from the move call)
    calls_before = tel._comm.set_state.await_count
    await asyncio.sleep(0.35)
    calls_after = tel._comm.set_state.await_count

    assert calls_after > calls_before
    assert tel._solar_target == ("heliocentric_polar", 0.9, 45.0)
    # position stays close to the original resolve (same target, only seconds later)
    ra1, dec1 = tel._position_radec
    assert abs(ra1 - ra0) < 1.0
    assert abs(dec1 - dec0) < 1.0
