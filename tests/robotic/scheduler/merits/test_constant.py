from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from astropy.time import Time


@pytest.mark.asyncio
async def test_constant_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = Task(1, "1", 100)

    merit = ConstantMerit(merit=10)
    assert await merit(time, task, data) == 10
