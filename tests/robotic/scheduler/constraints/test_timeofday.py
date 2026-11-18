from __future__ import annotations

from datetime import time as dtime

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import TimeOfDayConstraint
from pyobs.robotic.scheduler.constraints.timeofdayconstraint import TimeOfDayWindow
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.utils.time import Time


def _setup() -> tuple[DataProvider, Task]:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    return DataProvider(observer), Task(id=1, name="1", duration=100)


def _window(start: tuple[int, int], end: tuple[int, int]) -> TimeOfDayWindow:
    return TimeOfDayWindow(start=dtime(*start), end=dtime(*end))


@pytest.mark.asyncio
async def test_timeofday_constraint() -> None:
    data, task = _setup()
    constraint = TimeOfDayConstraint(windows=[_window((5, 0), (6, 0))])

    # same time of day on different dates
    assert await constraint(Time("2026-11-18T05:00:00"), task, data) is True
    assert await constraint(Time("2026-03-01T05:30:00"), task, data) is True
    assert await constraint(Time("2026-11-18T04:59:59"), task, data) is False
    assert await constraint(Time("2026-11-18T06:00:00"), task, data) is False  # half-open


@pytest.mark.asyncio
async def test_timeofday_constraint_wrap() -> None:
    data, task = _setup()
    constraint = TimeOfDayConstraint(windows=[_window((22, 0), (2, 0))])
    assert await constraint(Time("2026-11-18T23:00:00"), task, data) is True
    assert await constraint(Time("2026-11-18T01:00:00"), task, data) is True
    assert await constraint(Time("2026-11-18T12:00:00"), task, data) is False


@pytest.mark.asyncio
async def test_timeofday_constraint_multiple_windows() -> None:
    data, task = _setup()
    constraint = TimeOfDayConstraint(windows=[_window((5, 0), (6, 0)), _window((17, 0), (18, 0))])
    assert await constraint(Time("2026-11-18T05:30:00"), task, data) is True
    assert await constraint(Time("2026-11-18T17:30:00"), task, data) is True
    assert await constraint(Time("2026-11-18T12:00:00"), task, data) is False


def test_timeofday_constraint_astroplan() -> None:
    data, _ = _setup()
    constraint = TimeOfDayConstraint(windows=[_window((5, 0), (6, 0))])
    times = Time(["2026-11-18T04:00:00", "2026-11-18T05:30:00", "2026-11-19T05:30:00", "2026-11-19T07:00:00"])
    result = constraint.to_astroplan().compute_constraint(times, data.observer, None)
    assert result.tolist() == [False, True, True, False]


def test_timeofday_constraint_req_fields() -> None:
    constraint = TimeOfDayConstraint(windows=[_window((5, 0), (6, 0)), _window((17, 0), (18, 0))])
    assert constraint.req_fields() == {"WINDOWS": ("05:00-06:00,17:00-18:00", "UTC")}
    headers = constraint.get_fits_headers(1)
    assert list(headers) == ["HIERARCH REQ TOD WINDOWS"]
