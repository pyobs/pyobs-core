from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import BeforeTimeMerit
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_beforetime_merit() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    time = Time.now()
    task = Task(id=1, name="1", duration=100)

    merit = BeforeTimeMerit(time=time)
    assert await merit(time, task, data) == 1.0

    merit = BeforeTimeMerit(time=time)
    assert await merit(time - TimeDelta(5.0 * u.second), task, data) == 1.0

    merit = BeforeTimeMerit(time=time)
    assert await merit(time + TimeDelta(5.0 * u.second), task, data) == 0.0
