from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.targets import SiderealTarget
from astropy.time import Time


@pytest.mark.asyncio
async def test_airmass_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    coord = SkyCoord("6h23m58.2s -52d41m27.2s", frame="icrs")
    task = Task(
        id=1,
        name="Canopus",
        duration=100,
        target=SiderealTarget(ra=float(coord.ra.degree), dec=float(coord.dec.degree), name="Canopus"),
    )

    constraint = AirmassConstraint(max_airmass=1.3)

    time = Time("2025-11-03T17:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T19:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T21:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T23:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-04T01:00:00", scale="utc")
    assert await constraint(time, task, data) is True
