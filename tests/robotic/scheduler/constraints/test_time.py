from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import TimeConstraint
from pyobs.robotic.scheduler.targets import SiderealTarget
from astropy.time import Time


@pytest.mark.asyncio
async def test_time_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    coord = SkyCoord("6h23m58.2s -52d41m27.2s", frame="icrs")
    task = Task(
        id=1,
        name="Canopus",
        duration=100,
        target=SiderealTarget(ra=float(coord.ra.degree), dec=float(coord.dec.degree), name="Canopus"),
    )

    constraint = TimeConstraint(
        start=Time("2025-11-03T20:00:00", scale="utc"), end=Time("2025-11-03T23:00:00", scale="utc")
    )

    time = Time("2025-11-03T19:30:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T20:30:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-03T22:30:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-03T23:30:00", scale="utc")
    assert await constraint(time, task, data) is False
