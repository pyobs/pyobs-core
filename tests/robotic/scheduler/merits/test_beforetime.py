from __future__ import annotations
from astroplan import Observer
from astropy.coordinates import EarthLocation
import astropy.units as u

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import BeforeTimeMerit
from ..task import TestTask
from astropy.time import Time, TimeDelta


def test_beforetime_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = TestTask(1, "1", 100)

    merit = BeforeTimeMerit(time)
    assert merit(time, task, data) == 1.0

    merit = BeforeTimeMerit(time)
    assert merit(time - TimeDelta(5.0 * u.second), task, data) == 1.0

    merit = BeforeTimeMerit(time)
    assert merit(time + TimeDelta(5.0 * u.second), task, data) == 0.0
