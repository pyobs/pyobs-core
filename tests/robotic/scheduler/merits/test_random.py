from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import RandomMerit
from astropy.time import Time


@pytest.mark.asyncio
async def test_random_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = Task(1, "1", 100)

    # let somebody have fun when this fails
    merit = RandomMerit()
    assert -100.0 <= await merit(time, task, data) <= 100.0
