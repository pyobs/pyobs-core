from __future__ import annotations

import datetime
from unittest.mock import Mock

import numpy as np
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.utils import iers

from pyobs.robotic.scheduler.observingperiod import ObservingPeriods
from pyobs.utils.time import Time


@pytest.fixture
def offline_iers():
    with iers.conf.set_temp("auto_download", False), iers.conf.set_temp("auto_max_age", None):
        yield


def fixed_observer():
    observer = Mock(spec=Observer)

    def next_event(time, hour):
        date = time.to_datetime().date()
        event = Time(datetime.datetime.combine(date, datetime.time(hour)))
        if event <= time:
            event += datetime.timedelta(days=1)
        return event

    observer.sun_rise_time.side_effect = lambda time, which: next_event(time, 6)
    observer.sun_set_time.side_effect = lambda time, which: next_event(time, 18)
    return observer


@pytest.mark.parametrize("mode,hour", [("night", 6), ("day", 18)])
def test_exact_reset_and_half_open_boundaries(mode, hour):
    observer = fixed_observer()
    periods = ObservingPeriods(observer, mode)
    reset = Time(f"2026-10-13T{hour:02d}:00:00")
    before = reset - datetime.timedelta(microseconds=1)
    assert periods.key(before) == datetime.date(2026, 10, 12)
    assert periods.key(reset) == datetime.date(2026, 10, 13)
    start, end = periods.bounds(periods.key(reset), reset)
    assert start == reset
    assert periods.key(end) == datetime.date(2026, 10, 14)
    assert periods.bounds(periods.key(reset)) == (start, end)
    calls = observer.sun_rise_time.call_count + observer.sun_set_time.call_count
    periods.bounds(periods.key(reset), reset)
    assert observer.sun_rise_time.call_count + observer.sun_set_time.call_count == calls


@pytest.mark.parametrize("mode", ["night", "day"])
@pytest.mark.parametrize("longitude", [-70, 140, -170])
def test_real_periods_cross_utc_midnight_and_match_exact_events(mode, longitude, offline_iers):
    observer = Observer(location=EarthLocation.from_geodetic(longitude, -30, 200))
    periods = ObservingPeriods(observer, mode)
    time = Time("2026-10-13T03:00:00")
    start, end = periods.bounds(periods.key(time), time)
    assert start <= time < end
    assert start.to_datetime().date() != end.to_datetime().date()
    assert periods.bounds(periods.key(start), start) == (start, end)
    assert periods.bounds(periods.key(end), end)[0] == end
    assert periods.key(start - datetime.timedelta(seconds=1)) != periods.key(start)
    assert abs((end - start).sec - 86400) > 0.1


def test_mode_validation_and_mismatched_anchor():
    with pytest.raises(ValueError, match="mode"):
        ObservingPeriods(fixed_observer(), "invalid")
    periods = ObservingPeriods(fixed_observer())
    with pytest.raises(ValueError, match="does not match"):
        periods.bounds(datetime.date(2026, 10, 13), Time("2026-10-13T03:00:00"))


@pytest.mark.parametrize("bad", [Time(np.ma.array(2451545.0, mask=True), format="jd"), np.nan])
def test_missing_or_nonfinite_events_fail(bad):
    observer = Mock(spec=Observer)
    observer.sun_rise_time.return_value = bad
    with pytest.raises(ValueError, match="finite solar reset"):
        ObservingPeriods(observer).bounds(datetime.date(2026, 10, 13))


def test_missing_and_ambiguous_date_keys():
    observer = Mock(spec=Observer)
    observer.sun_rise_time.return_value = Time("2026-10-14T06:00:00")
    with pytest.raises(ValueError, match="no solar reset event"):
        ObservingPeriods(observer).bounds(datetime.date(2026, 10, 13))
    observer.sun_rise_time.side_effect = [
        Time("2026-10-13T00:00:00"),
        Time("2026-10-13T23:59:00"),
        Time("2026-10-14T23:58:00"),
    ]
    with pytest.raises(ValueError, match="Ambiguous"):
        ObservingPeriods(observer).bounds(datetime.date(2026, 10, 13))


@pytest.mark.parametrize("mode", ["night", "day"])
def test_exact_utc_midnight_event_and_time_scale(mode):
    observer = fixed_observer()

    def midnight(time, which):
        date = time.utc.to_datetime().date() + datetime.timedelta(days=1)
        return Time(datetime.datetime.combine(date, datetime.time()), scale="utc")

    event = observer.sun_rise_time if mode == "night" else observer.sun_set_time
    event.side_effect = midnight
    periods = ObservingPeriods(observer, mode)
    time = Time("2026-10-13T00:00:00", scale="utc")
    assert periods.key(time) == datetime.date(2026, 10, 13)
    assert periods.key(Time(time.tai)) == periods.key(time)
    assert periods.bounds(periods.key(time), time)[0] == time
