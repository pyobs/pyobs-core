from __future__ import annotations
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from ..task import TestTask
from astropy.time import Time


def test_constant_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = TestTask(1, "1", 100)

    merit = ConstantMerit(10)
    assert merit(time, task, data) == 10
