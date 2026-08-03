from __future__ import annotations

import astropy.units as u
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.utils.time import Time


def make_observer() -> Observer:
    return Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


# ── cache hit/miss ───────────────────────────────────────────────────────────


def test_sun_is_cached_per_time(mocker) -> None:
    import astropy.coordinates

    data = DataProvider(make_observer())
    spy = mocker.patch(
        "pyobs.robotic.scheduler.dataprovider.astropy.coordinates.get_sun", wraps=astropy.coordinates.get_sun
    )

    t1 = Time("2025-11-03T18:00:00", scale="utc")
    t2 = Time("2025-11-03T19:00:00", scale="utc")

    data.sun(t1)
    data.sun(t1)  # cache hit, same time
    data.sun(t2)  # cache miss, different time

    assert spy.call_count == 2


def test_sun_altaz_is_cached_per_time(mocker) -> None:
    observer = make_observer()
    data = DataProvider(observer)
    spy = mocker.spy(observer, "sun_altaz")

    t1 = Time("2025-11-03T18:00:00", scale="utc")
    t2 = Time("2025-11-03T19:00:00", scale="utc")

    data.sun_altaz(t1)
    data.sun_altaz(t1)
    data.sun_altaz(t2)

    assert spy.call_count == 2


def test_moon_is_cached_per_time(mocker) -> None:
    import astropy.coordinates

    data = DataProvider(make_observer())
    spy = mocker.patch(
        "pyobs.robotic.scheduler.dataprovider.astropy.coordinates.get_body", wraps=astropy.coordinates.get_body
    )

    t1 = Time("2025-11-03T18:00:00", scale="utc")
    t2 = Time("2025-11-03T19:00:00", scale="utc")

    data.moon(t1)
    data.moon(t1)
    data.moon(t2)

    assert spy.call_count == 2


def test_moon_illumination_is_cached_per_time(mocker) -> None:
    observer = make_observer()
    data = DataProvider(observer)
    spy = mocker.spy(observer, "moon_illumination")

    t1 = Time("2025-11-03T18:00:00", scale="utc")
    t2 = Time("2025-11-03T19:00:00", scale="utc")

    data.moon_illumination(t1)
    data.moon_illumination(t1)
    data.moon_illumination(t2)

    assert spy.call_count == 2


# ── per-instance isolation ────────────────────────────────────────────────────


def test_cache_does_not_leak_across_instances(mocker) -> None:
    """Each DataProvider (one per schedule() call) must not see another instance's cached
    values -- a leak here would mean a later schedule run silently reuses stale sun/moon
    data from an earlier one."""
    observer = make_observer()
    data1 = DataProvider(observer)
    data2 = DataProvider(observer)
    spy = mocker.spy(observer, "moon_illumination")

    t = Time("2025-11-03T18:00:00", scale="utc")

    data1.moon_illumination(t)
    data2.moon_illumination(t)

    # both instances call through -- no cross-instance cache hit
    assert spy.call_count == 2
