from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from pydantic import ValidationError

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import RandomMerit
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_random_merit() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    time = Time.now()
    task = Task(id=1, name="1", duration=100)

    merit = RandomMerit()
    values = [await merit(time, task, data) for _ in range(2000)]
    assert min(values) >= 0.0
    assert abs(sum(values) / len(values) - 1.0) < 0.02


@pytest.mark.asyncio
async def test_random_merit_clipped_at_zero() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)

    merit = RandomMerit(std=1.0)
    values = [await merit(Time.now(), task, data) for _ in range(2000)]
    assert min(values) == 0.0


def test_random_merit_std_bounds() -> None:
    with pytest.raises(ValidationError):
        RandomMerit(std=1.5)
