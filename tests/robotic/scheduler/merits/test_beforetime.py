from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
import astropy.units as u

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import BeforeTimeMerit
from astropy.time import Time, TimeDelta


@pytest.mark.asyncio
async def test_beforetime_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = Task(id=1, name="1", duration=100 * u.second)

    merit = BeforeTimeMerit(time=time)
    assert await merit(time, task, data) == 1.0

    merit = BeforeTimeMerit(time=time)
    assert await merit(time - TimeDelta(5.0 * u.second), task, data) == 1.0

    merit = BeforeTimeMerit(time=time)
    assert await merit(time + TimeDelta(5.0 * u.second), task, data) == 0.0
