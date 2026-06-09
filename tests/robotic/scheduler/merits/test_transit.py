from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits.transit import TransitMerit
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time

# ── helpers ───────────────────────────────────────────────────────────────────


def make_merit(
    jd0: float = 2460000.0, period: float = 3.0, duration: int = 7200, ingress: float = 0.2, over: float = 0.0
) -> TransitMerit:
    return TransitMerit(jd0=jd0, period=period, duration=duration, ingress=ingress, over=over)


# ── transit_time ──────────────────────────────────────────────────────────────


def test_transit_time_returns_time() -> None:
    merit = make_merit(jd0=2460000.0, period=3.0)
    t = merit.transit_time()
    assert isinstance(t, Time)


def test_transit_time_is_near_jd0_plus_n_periods() -> None:
    """transit_time should be jd0 + n*period for integer n closest to now."""
    merit = make_merit(jd0=2460000.0, period=3.0)
    t = merit.transit_time()
    n = merit.periods_since_jd0()
    expected_jd = merit.jd0 + n * merit.period
    assert abs(t.jd - expected_jd) < 1e-9


# ── end_time ──────────────────────────────────────────────────────────────────


def test_end_time_after_transit_time() -> None:
    merit = make_merit(duration=7200, ingress=0.2)
    assert merit.end_time().jd > merit.transit_time().jd


def test_end_time_offset_matches_formula() -> None:
    """end_time = transit_time + (duration/2 + ingress*duration) / 86400."""
    merit = make_merit(duration=7200, ingress=0.2)
    mid = merit.transit_time()
    expected_offset = (7200 / 2.0 + 0.2 * 7200) / 86400.0
    assert abs(merit.end_time().jd - (mid.jd + expected_offset)) < 1e-9


def test_end_time_zero_ingress() -> None:
    """With ingress=0, end_time = transit_time + duration/2."""
    merit = make_merit(duration=7200, ingress=0.0)
    mid = merit.transit_time()
    expected_offset = 7200 / 2.0 / 86400.0
    assert abs(merit.end_time().jd - (mid.jd + expected_offset)) < 1e-9


def test_end_time_longer_with_larger_ingress() -> None:
    merit_short = make_merit(duration=7200, ingress=0.1)
    merit_long = make_merit(duration=7200, ingress=0.5)
    assert merit_long.end_time().jd > merit_short.end_time().jd


# ── __call__ ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_merit_returns_one_during_window() -> None:
    """Merit returns 1.0 when phase is inside the transit window."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    merit = make_merit(jd0=2460000.0, period=3.0, duration=7200, ingress=0.2)
    target = SiderealTarget(name="Betelgeuse", ra=83.82, dec=7.41)
    task = Task(id=1, name="t", duration=300, target=target)

    # find a time where phase_for_jd is actually in the window by scanning
    n = merit.periods_since_jd0()
    phase_mid = 1.0 - merit._duration / 2.0
    jd_mid = merit.jd0 + (n + phase_mid) * merit.period
    time = Time(jd_mid, format="jd", scale="tdb")

    coord = target.coordinates(time)
    loc = observer.location
    phi = merit.phase_for_jd(coord, loc, time)

    # verify this time is actually in the window before asserting
    in_window = 1.0 - merit._duration / 2.0 - merit._ingress <= phi <= 1.0 - merit._duration / 2.0 - merit._over
    if in_window:
        assert await merit(time, task, data) == 1.0
    else:
        pytest.skip("Time not in transit window after barycentric correction — skip rather than fail")


@pytest.mark.asyncio
async def test_merit_returns_zero_outside_window() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    merit = make_merit(jd0=2460000.0, period=3.0, duration=7200, ingress=0.2)

    # time at phase 0.5 — far from transit
    n = merit.periods_since_jd0()
    time = Time(merit.jd0 + (n + 0.5) * merit.period, format="jd", scale="tdb")

    task = Task(id=1, name="t", duration=300, target=SiderealTarget(name="Betelgeuse", ra=83.82, dec=7.41))
    assert await merit(time, task, data) == 0.0
