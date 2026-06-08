from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import MoonIlluminationConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_moonillumination_constraint() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)
    constraint = MoonIlluminationConstraint(max_phase=0.5)

    time = Time("2025-11-05T13:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-12T05:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-12T08:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-13T0:00:00", scale="utc")
    assert await constraint(time, task, data) is True
