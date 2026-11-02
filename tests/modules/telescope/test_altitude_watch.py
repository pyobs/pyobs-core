"""min_altitude is enforced while tracking, not only on moves (pyobs-core#1023)."""

import logging
from unittest.mock import AsyncMock

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.utils import iers

from pyobs.interfaces import TrackingMode
from pyobs.modules.telescope import DummyRaDecTelescope
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.utils.enums import MotionStatus
from pyobs.utils.time import Time
from tests.modules.telescope.test_basetelescope import make_dummyradectelescope
from tests.modules.telescope.test_geometry_headers import PositionTelescope

T0 = Time("2026-10-13T20:00:00")
STEP = 5.0  # seconds, like the watch interval


@pytest.fixture(autouse=True)
def offline_iers():
    with iers.conf.set_temp("auto_download", False), iers.conf.set_temp("auto_max_age", None):
        yield


def _observer() -> Observer:
    return Observer(latitude=52 * u.deg, longitude=10 * u.deg, elevation=100 * u.m)


def _icrs_at(alt: float, az: float, when: Time = T0) -> tuple[float, float]:
    """RA/Dec that is at the given alt/az at the given time."""
    obs = _observer()
    icrs = SkyCoord(alt=alt * u.deg, az=az * u.deg, obstime=when, location=obs.location, frame="altaz").icrs
    return float(icrs.ra.degree), float(icrs.dec.degree)


def _at(seconds: float) -> Time:
    return T0 + seconds * u.s


async def _tracking_tel(alt: float = 10.2, az: float = 270.0, **kwargs) -> DummyRaDecTelescope:
    """Dummy telescope pointing at a western (sinking) position, TRACKING."""
    kwargs.setdefault("min_altitude", 10.0)
    tel = make_dummyradectelescope(position=_icrs_at(alt, az), **kwargs)
    await tel._change_motion_status(MotionStatus.TRACKING)
    tel.stop_motion = AsyncMock()
    tel.park = AsyncMock()
    return tel


async def _run_until_below(tel: DummyRaDecTelescope, steps: int = 400) -> int:
    """Tick every STEP seconds; return the tick at which an action fired."""
    for i in range(steps):
        await tel._altitude_watch_tick(now=_at(i * STEP))
        if tel._altitude_action_fired:
            return i
    raise AssertionError("never fired")


@pytest.mark.asyncio
async def test_sinking_below_limit_stops_once(caplog):
    tel = await _tracking_tel()
    tel._tracked_body = "mars"
    tel.set_tracking_mode = AsyncMock()

    with caplog.at_level(logging.ERROR):
        await _run_until_below(tel)
        for i in range(400, 410):
            await tel._altitude_watch_tick(now=_at(i * STEP))

    tel.stop_motion.assert_awaited_once()
    tel.set_tracking_mode.assert_awaited_once_with(TrackingMode.OFF)
    assert tel._tracked_body is None and tel._tracked_elements is None
    assert len([r for r in caplog.records if "below altitude limit" in r.message]) == 1


@pytest.mark.asyncio
async def test_stops_close_to_limit_not_at_horizon():
    tel = await _tracking_tel()
    i = await _run_until_below(tel)
    alt = tel._altitude_prev
    assert i > 0
    assert 10.0 - 0.2 < alt < 10.0


@pytest.mark.asyncio
async def test_first_sample_never_fires():
    tel = await _tracking_tel(alt=9.0)
    await tel._altitude_watch_tick(now=T0)
    tel.stop_motion.assert_not_awaited()
    await tel._altitude_watch_tick(now=_at(STEP))
    tel.stop_motion.assert_awaited_once()


@pytest.mark.asyncio
async def test_rising_target_below_limit_is_left_alone():
    tel = await _tracking_tel(alt=5.0, az=90.0)
    for i in range(10):
        await tel._altitude_watch_tick(now=_at(i * STEP))
    tel.stop_motion.assert_not_awaited()


@pytest.mark.asyncio
async def test_rearm_needs_hysteresis():
    tel = await _tracking_tel(alt=9.0)
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    assert tel._altitude_action_fired

    # between min and min + 0.5: stays fired
    tel._position = SkyCoord(*_icrs_at(10.2, 270.0, _at(2 * STEP)), unit="deg", frame="icrs")
    await tel._altitude_watch_tick(now=_at(2 * STEP))
    assert tel._altitude_action_fired

    # clearly above: re-armed
    tel._position = SkyCoord(*_icrs_at(20.0, 270.0, _at(3 * STEP)), unit="deg", frame="icrs")
    await tel._altitude_watch_tick(now=_at(3 * STEP))
    assert not tel._altitude_action_fired


@pytest.mark.asyncio
async def test_move_radec_rearms():
    tel = await _tracking_tel(alt=9.0)
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    assert tel._altitude_action_fired

    tel._move_radec = AsyncMock()
    await tel.move_radec(*_icrs_at(40.0, 180.0, Time.now()))
    assert not tel._altitude_action_fired
    assert tel._altitude_prev is None


@pytest.mark.asyncio
async def test_slew_lock_skips_and_clears_previous_sample():
    tel = await _tracking_tel(alt=9.0)
    await tel._altitude_watch_tick(now=T0)
    assert tel._altitude_prev is not None
    async with tel._lock_moving:
        await tel._altitude_watch_tick(now=_at(STEP))
    assert tel._altitude_prev is None
    tel.stop_motion.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        MotionStatus.PARKED,
        MotionStatus.PARKING,
        MotionStatus.ERROR,
        MotionStatus.INITIALIZING,
        MotionStatus.ABORTING,
        MotionStatus.SLEWING,
    ],
)
async def test_ineligible_states_do_nothing(status):
    tel = await _tracking_tel(alt=9.0)
    await tel._change_motion_status(status)
    for i in range(5):
        await tel._altitude_watch_tick(now=_at(i * STEP))
    tel.stop_motion.assert_not_awaited()
    tel.park.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_state_is_eligible():
    tel = await _tracking_tel(alt=9.0)
    await tel._change_motion_status(MotionStatus.UNKNOWN)
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    tel.stop_motion.assert_awaited_once()


@pytest.mark.asyncio
async def test_park_action_parks_and_clears_tracking():
    tel = await _tracking_tel(alt=9.0, altitude_action="park")
    tel._tracked_body = "moon"
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    tel.park.assert_awaited_once()
    tel.stop_motion.assert_not_awaited()
    assert tel._tracked_body is None


@pytest.mark.asyncio
async def test_none_action_only_logs(caplog):
    tel = await _tracking_tel(alt=9.0, altitude_action="none")
    with caplog.at_level(logging.ERROR):
        for i in range(6):
            await tel._altitude_watch_tick(now=_at(i * STEP))
    tel.stop_motion.assert_not_awaited()
    tel.park.assert_not_awaited()
    assert len([r for r in caplog.records if "below altitude limit" in r.message]) == 1


def test_invalid_action_raises():
    with pytest.raises(ValueError):
        make_dummyradectelescope(altitude_action="explode")


@pytest.mark.asyncio
async def test_missing_position_or_observer_is_harmless(mocker):
    tel = await _tracking_tel(alt=9.0)
    mocker.patch.object(DummyRaDecTelescope, "_position_radec", new_callable=mocker.PropertyMock, return_value=None)
    await tel._altitude_watch_tick(now=T0)
    mocker.patch.object(
        DummyRaDecTelescope, "_position_radec", new_callable=mocker.PropertyMock, return_value=(float("nan"), 0.0)
    )
    await tel._altitude_watch_tick(now=T0)
    tel._observer = None
    await tel._altitude_watch_tick(now=T0)
    tel.stop_motion.assert_not_awaited()


@pytest.mark.asyncio
async def test_failing_action_is_retried_and_does_not_raise(caplog):
    tel = await _tracking_tel(alt=9.0)
    tel.stop_motion = AsyncMock(side_effect=RuntimeError("boom"))
    await tel._altitude_watch_tick(now=T0)
    with caplog.at_level(logging.ERROR):
        await tel._altitude_watch_tick(now=_at(STEP))
        assert not tel._altitude_action_fired
        tel.stop_motion = AsyncMock()
        await tel._altitude_watch_tick(now=_at(2 * STEP))
    assert tel._altitude_action_fired
    tel.stop_motion.assert_awaited_once()


@pytest.mark.asyncio
async def test_track_refresh_does_not_nudge_after_stop(mocker):
    tel = await _tracking_tel(alt=9.0)
    tel._tracked_body = "mars"
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    tel._move_radec = AsyncMock()
    await tel._track_refresh_tick()
    tel._move_radec.assert_not_awaited()


@pytest.mark.asyncio
async def test_real_stop_motion_does_not_deadlock():
    """The watch must not hold _lock_moving when calling the real stop_motion."""
    tel = make_dummyradectelescope(position=_icrs_at(9.0, 270.0), min_altitude=10.0)
    await tel._change_motion_status(MotionStatus.TRACKING)
    await tel._altitude_watch_tick(now=T0)
    await tel._altitude_watch_tick(now=_at(STEP))
    assert tel._altitude_action_fired
    assert tel.motion_status() == MotionStatus.IDLE


def test_warns_without_position_override(caplog):
    class Bare(BaseTelescope):
        async def _move_radec(self, ra, dec, abort_event): ...
        async def _move_altaz(self, alt, az, abort_event): ...
        async def _set_tracking_rate(self, ra_rate, dec_rate): ...
        async def init(self, **kwargs): ...
        async def park(self, **kwargs): ...
        async def stop_motion(self, **kwargs): ...

    with caplog.at_level(logging.WARNING):
        Bare(observer=_observer())._warn_if_unprotected()
    assert any("_position_radec" in r.message for r in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        PositionTelescope(observer=_observer())._warn_if_unprotected()
        make_dummyradectelescope()._warn_if_unprotected()
        Bare(observer=_observer(), altitude_action="none")._warn_if_unprotected()
    assert not caplog.records
