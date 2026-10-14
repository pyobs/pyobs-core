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


def masked_event():
    return Time(np.ma.array(2451545.0, mask=True), format="jd")


@pytest.mark.parametrize("mode,hour", [("night", 6), ("day", 18)])
def test_masked_follow_up_preserves_valid_reset_and_cache(mode, hour):
    observer = fixed_observer()

    def event_with_empty_follow_up(time, which):
        date = time.utc.to_datetime().date()
        reset = Time(datetime.datetime.combine(date, datetime.time(hour)))
        if time < reset:
            return reset
        if time.utc.to_datetime().hour == 23:
            return reset + datetime.timedelta(days=1)
        return masked_event()

    event_func = observer.sun_rise_time if mode == "night" else observer.sun_set_time
    event_func.side_effect = event_with_empty_follow_up
    periods = ObservingPeriods(observer, mode)
    reset = Time(f"2026-10-13T{hour:02d}:00:00")
    start, end = periods.bounds(periods.key(reset), reset)
    assert start == reset
    assert end == reset + datetime.timedelta(days=1)
    assert periods.bounds(periods.key(reset)) == (start, end)
    calls = event_func.call_count
    assert periods.bounds(periods.key(reset), reset) == (start, end)
    assert event_func.call_count == calls
    assert periods.key(start - datetime.timedelta(microseconds=1)) != periods.key(start)
    assert periods.key(end) == datetime.date(2026, 10, 14)


@pytest.mark.parametrize("mode", ["night", "day"])
@pytest.mark.parametrize("entry", ["key", "anchored", "date_only"])
def test_two_events_then_masked_follow_up_is_ambiguous(mode, entry):
    observer = fixed_observer()
    event_func = observer.sun_rise_time if mode == "night" else observer.sun_set_time
    event_func.side_effect = [Time("2026-10-13T00:00:00"), Time("2026-10-13T23:59:00"), masked_event()]
    with pytest.raises(ValueError, match="Ambiguous"):
        periods = ObservingPeriods(observer, mode)
        time = Time("2026-10-13T12:00:00")
        if entry == "key":
            periods.key(time)
        else:
            periods.bounds(datetime.date(2026, 10, 13), time if entry == "anchored" else None)


@pytest.mark.parametrize("bad", [np.nan, Time("2026-10-13T06:00:00"), Time("2026-10-13T05:00:00"), "invalid"])
def test_invalid_follow_up_still_fails(bad):
    observer = fixed_observer()
    observer.sun_rise_time.side_effect = [Time("2026-10-13T06:00:00"), bad]
    with pytest.raises(ValueError):
        ObservingPeriods(observer).bounds(datetime.date(2026, 10, 13))


def test_valid_reset_does_not_fabricate_missing_closing_event():
    observer = fixed_observer()
    observer.sun_rise_time.side_effect = [Time("2026-10-13T06:00:00"), masked_event(), masked_event()]
    with pytest.raises(ValueError, match="finite solar reset"):
        ObservingPeriods(observer).bounds(datetime.date(2026, 10, 13))


def test_reset_near_date_end_keeps_its_exact_time():
    observer = fixed_observer()
    reset = Time("2026-10-13T23:59:30")
    observer.sun_rise_time.side_effect = [reset, masked_event()]
    assert ObservingPeriods(observer)._events(datetime.date(2026, 10, 13)) == (reset,)


@pytest.mark.parametrize("mode", ["night", "day"])
def test_real_polar_missing_first_event_still_fails(mode, offline_iers):
    from astroplan import TargetAlwaysUpWarning

    observer = Observer(location=EarthLocation.from_geodetic(0, 89, 0))
    with pytest.warns(TargetAlwaysUpWarning), pytest.raises(ValueError, match="finite solar reset"):
        ObservingPeriods(observer, mode).bounds(datetime.date(2026, 6, 21))


@pytest.mark.parametrize(
    "longitude,latitude,mode,month,hour",
    [(-76, 41.2, "night", 10, 3), (9.9445, 51.5606, "night", 10, 3), (9.9445, 51.5606, "day", 4, 14)],
)
@pytest.mark.parametrize("day", range(10, 17))
def test_northern_resets_moving_later_than_search_step(longitude, latitude, mode, month, hour, day, offline_iers):
    from pyobs.robotic.scheduler import DataProvider

    observer = Observer(location=EarthLocation.from_geodetic(longitude, latitude, 200))
    data = DataProvider(observer, mode=mode)
    time = Time(f"2026-{month:02d}-{day:02d}T{hour:02d}:00:00")
    start, end = data.period_bounds(time)
    assert (end - start).sec > 86460
    assert start <= time < end
    assert data.archive.periods.bounds(data.night(time)) == (start, end)
    assert data.period_bounds(start) == (start, end)
    assert data.night(start - datetime.timedelta(microseconds=1)) != data.night(start)
    assert data.period_bounds(end)[0] == end
    assert data.period_bounds(Time(time.tai)) == (start, end)


def test_only_expected_follow_up_warnings_are_suppressed():
    import warnings

    from astroplan import TargetNeverUpWarning

    observer = fixed_observer()
    calls = 0

    def lookup(time, which):
        nonlocal calls
        calls += 1
        warnings.warn("solar search", TargetNeverUpWarning)
        if calls == 1:
            return Time("2026-10-13T06:00:00")
        warnings.warn("unrelated diagnostic", UserWarning)
        return masked_event()

    observer.sun_rise_time.side_effect = lookup
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = ObservingPeriods(observer)._events(datetime.date(2026, 10, 13))
    assert len(result) == 1
    assert [(w.category, str(w.message)) for w in caught] == [
        (TargetNeverUpWarning, "solar search"),
        (UserWarning, "unrelated diagnostic"),
    ]


@pytest.mark.asyncio
async def test_missing_closing_reset_fails_before_archive_io():
    from unittest.mock import AsyncMock

    from pyobs.robotic.scheduler.observationarchiveevolution import ObservationArchiveEvolution

    observer = fixed_observer()
    observer.sun_rise_time.side_effect = [Time("2026-10-13T06:00:00"), masked_event(), masked_event()]
    archive = AsyncMock()
    with pytest.raises(ValueError, match="finite solar reset"):
        await ObservationArchiveEvolution(observer, archive).observations_for_night(datetime.date(2026, 10, 13))
    archive.get_observations.assert_not_called()


def test_nonincreasing_beyond_date_result_still_fails():
    observer = fixed_observer()
    observer.sun_rise_time.side_effect = [Time("2026-10-13T23:59:30"), Time("2026-10-14T00:00:10")]
    with pytest.raises(ValueError, match="must increase"):
        ObservingPeriods(observer)._events(datetime.date(2026, 10, 13))


def test_event_enumeration_is_bounded():
    observer = fixed_observer()
    observer.sun_rise_time.side_effect = [
        Time("2026-10-13T00:00:00"),
        Time("2026-10-13T12:00:00"),
        Time("2026-10-13T23:00:00"),
    ]
    with pytest.raises(ValueError, match="Too many"):
        ObservingPeriods(observer)._events(datetime.date(2026, 10, 13))
    assert observer.sun_rise_time.call_count == 3


@pytest.mark.parametrize("mode", ["night", "day"])
def test_missing_first_reset_is_not_accepted(mode):
    observer = fixed_observer()
    event_func = observer.sun_rise_time if mode == "night" else observer.sun_set_time
    event_func.return_value = masked_event()
    event_func.side_effect = None
    with pytest.raises(ValueError, match="finite solar reset"):
        ObservingPeriods(observer, mode).bounds(datetime.date(2026, 10, 13))
