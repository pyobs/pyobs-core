from __future__ import annotations
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time, TimeDelta
import astropy.units as u

from pyobs.robotic import Task, Observation
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import PerNightMerit
from pyobs.robotic.scheduler.observationarchiveevolution import ObservationArchiveEvolution


@pytest.mark.asyncio
async def test_pernight_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    archive = ObservationArchiveEvolution(observer)
    data = DataProvider(observer, archive)
    time = Time.now()
    task = Task(1, "1", 100)
    scheduled_task = Observation(task, time, time + TimeDelta(5.0 * u.minute))

    merit = PerNightMerit(count=2)
    assert await merit(time, task, data) == 1.0

    await archive.evolve(scheduled_task)
    assert await merit(time, task, data) == 1.0

    await archive.evolve(scheduled_task)
    assert await merit(time, task, data) == 0.0

    await archive.evolve(scheduled_task)
    assert await merit(time, task, data) == 0.0
