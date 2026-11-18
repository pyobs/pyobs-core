from __future__ import annotations

from datetime import time as dtime

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits.timeofday import TimeOfDayMerit, TimeOfDayWindow
from pyobs.utils.time import Time


def _setup() -> tuple[DataProvider, Task]:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    return DataProvider(observer), Task(id=1, name="1", duration=100)


@pytest.mark.asyncio
async def test_timeofday_merit() -> None:
    data, task = _setup()
    merit = TimeOfDayMerit(windows=[TimeOfDayWindow(start=dtime(5, 0), end=dtime(6, 0))])

    # same time of day on different dates
    assert await merit(Time("2026-11-18T05:00:00"), task, data) == 1.0
    assert await merit(Time("2026-03-01T05:30:00"), task, data) == 1.0
    assert await merit(Time("2026-11-18T04:59:59"), task, data) == 0.0
    assert await merit(Time("2026-11-18T06:00:00"), task, data) == 0.0  # half-open


@pytest.mark.asyncio
async def test_timeofday_merit_wrap_and_inverse() -> None:
    data, task = _setup()
    merit = TimeOfDayMerit(windows=[TimeOfDayWindow(start=dtime(22, 0), end=dtime(2, 0))])
    assert await merit(Time("2026-11-18T23:00:00"), task, data) == 1.0
    assert await merit(Time("2026-11-18T01:00:00"), task, data) == 1.0
    assert await merit(Time("2026-11-18T12:00:00"), task, data) == 0.0

    merit = TimeOfDayMerit(windows=[TimeOfDayWindow(start=dtime(5, 0), end=dtime(6, 0))], inverse=True)
    assert await merit(Time("2026-11-18T05:30:00"), task, data) == 0.0
    assert await merit(Time("2026-11-18T12:00:00"), task, data) == 1.0


@pytest.mark.asyncio
async def test_timeofday_merit_multiple_windows() -> None:
    data, task = _setup()
    merit = TimeOfDayMerit(
        windows=[
            TimeOfDayWindow(start=dtime(5, 0), end=dtime(6, 0)),
            TimeOfDayWindow(start=dtime(17, 0), end=dtime(18, 0)),
        ]
    )
    assert await merit(Time("2026-11-18T05:30:00"), task, data) == 1.0
    assert await merit(Time("2026-11-18T17:30:00"), task, data) == 1.0
    assert await merit(Time("2026-11-18T12:00:00"), task, data) == 0.0
