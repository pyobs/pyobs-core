from __future__ import annotations

import warnings
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import astropy.units as u
import pytest
from astroplan import Observer, TargetAlwaysUpWarning, TargetNeverUpWarning
from astropy.coordinates import EarthLocation
from astropy.utils import iers

from pyobs.utils.time import Time

# a mid-latitude site, where the sun rises and sets every day
MID_LATITUDE_LOCATION = EarthLocation.from_geodetic(lon=10 * u.deg, lat=50 * u.deg, height=500 * u.m)

# a site above the Arctic circle, which experiences polar day/night
POLAR_LOCATION = EarthLocation.from_geodetic(lon=10 * u.deg, lat=70 * u.deg, height=500 * u.m)


def test_night_obs_uses_sunset_date() -> None:
    observer = Observer(location=MID_LATITUDE_LOCATION, timezone="UTC")
    t = Time("2026-07-16T15:45:50")
    assert t.night_obs(observer) == t.to_datetime().date()


def test_night_obs_stays_on_previous_night_past_equinox_sunrise() -> None:
    # near the equinox, sunset + 12h lands close to sunrise -- a query shortly after sunrise
    # (e.g. a morning calibration script) must still resolve to the night that just ended, not
    # flip to the following night.
    observer = Observer(location=MID_LATITUDE_LOCATION, timezone="UTC")
    before_flip = Time("2026-09-23T05:00:00")
    after_flip = Time("2026-09-23T07:00:00")

    night_before = before_flip.night_obs(observer)
    night_after = after_flip.night_obs(observer)

    assert night_before == night_after == before_flip.to_datetime().date() - timedelta(days=1)


def test_night_obs_falls_back_to_local_date_during_polar_day() -> None:
    observer = Observer(location=POLAR_LOCATION, timezone="UTC")
    t = Time("2026-07-16T15:45:50")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        night = t.night_obs(observer)

    assert night == t.to_datetime(timezone=observer.timezone).date()


@pytest.fixture(autouse=True)
def offline_iers():
    with iers.conf.set_temp("auto_download", False):
        yield


@pytest.mark.parametrize(
    "longitude, latitude, timezone, start, expected",
    [
        (-76, 41.2, "UTC", "2026-10-14T12:00:00", date(2026, 10, 14)),
        (-76, 41.2, "America/New_York", "2026-10-14T12:00:00", date(2026, 10, 14)),
        (-118.24, 34.05, "America/Los_Angeles", "2026-06-20T12:00:00", date(2026, 6, 20)),
        (151.21, -33.87, "Australia/Sydney", "2026-10-14T12:00:00", date(2026, 10, 14)),
    ],
)
def test_night_obs_stable_from_local_noon_until_next_noon(longitude, latitude, timezone, start, expected):
    observer = Observer(location=EarthLocation.from_geodetic(longitude, latitude), timezone=timezone)
    noon = observer.timezone.localize(datetime.fromisoformat(start))
    # Sample sunset, both midnights and dawn without relying on exact solar-event times.
    for minutes in range(0, 24 * 60, 30):
        assert Time(noon + timedelta(minutes=minutes)).night_obs(observer) == expected
    next_noon = noon + timedelta(days=1)
    assert Time(next_noon - timedelta(microseconds=1)).night_obs(observer) == expected
    for offset in (0, 1):
        assert Time(next_noon + timedelta(microseconds=offset)).night_obs(observer) == expected + timedelta(days=1)


@pytest.mark.parametrize("timezone", ["America/New_York", ZoneInfo("America/New_York")])
@pytest.mark.parametrize(
    "query, anchor, expected",
    [
        ("2026-03-08T07:30:00", "2026-03-07T17:00:00", date(2026, 3, 7)),
        ("2026-11-01T07:30:00", "2026-10-31T16:00:00", date(2026, 10, 31)),
    ],
)
def test_night_obs_localizes_noon_with_its_own_dst_offset(mocker, timezone, query, anchor, expected):
    observer = Observer(location=EarthLocation.from_geodetic(-76, 41.2), timezone=timezone)
    search = mocker.spy(observer, "sun_set_time")
    assert Time(query).night_obs(observer) == expected
    searched_time = search.call_args.args[0]
    assert abs((searched_time - Time(anchor)).to_value(u.second)) < 1e-6
    assert search.call_args.kwargs == {"which": "next"}


@pytest.mark.parametrize("month, warning", [(6, TargetAlwaysUpWarning), (12, TargetNeverUpWarning)])
@pytest.mark.parametrize("hour", [0, 6, 18, 23])
def test_night_obs_polar_fallback_uses_query_local_date(month, warning, hour):
    observer = Observer(location=EarthLocation.from_geodetic(15.6, 78.2), timezone="Europe/Oslo")
    local = observer.timezone.localize(datetime(2026, month, 20, hour))
    with pytest.warns(warning):
        assert Time(local).night_obs(observer) == date(2026, month, 20)
