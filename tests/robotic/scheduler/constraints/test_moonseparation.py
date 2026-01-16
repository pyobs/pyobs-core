from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import MoonSeparationConstraint
from pyobs.robotic.scheduler.targets import SiderealTarget
from astropy.time import Time


@pytest.mark.asyncio
async def test_moonseparation_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    task = Task(1, "Antares", 100)
    task._target = SiderealTarget("Antares", SkyCoord("16h29m22.94s -26d25m53.0s", frame="icrs"))

    constraint = MoonSeparationConstraint(20.0)

    time = Time("2025-11-18T15:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-19T11:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-19T17:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-19T23:00:00", scale="utc")
    assert await constraint(time, task, data) is False
