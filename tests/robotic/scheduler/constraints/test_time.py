from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import TimeConstraint
from pyobs.robotic.scheduler.targets import SiderealTarget
from ..task import TestTask
from astropy.time import Time


@pytest.mark.asyncio
async def test_time_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    task = TestTask(1, "Canopus", 100)
    task._target = SiderealTarget("Canopus", SkyCoord("6h23m58.2s -52d41m27.2s", frame="icrs"))

    constraint = TimeConstraint(Time("2025-11-03T20:00:00", scale="utc"), Time("2025-11-03T23:00:00", scale="utc"))

    time = Time("2025-11-03T19:30:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T20:30:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-03T22:30:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-03T23:30:00", scale="utc")
    assert await constraint(time, task, data) is False
