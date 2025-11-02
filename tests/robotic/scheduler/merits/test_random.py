from __future__ import annotations
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import RandomMerit
from ..task import TestTask
from astropy.time import Time


def test_random_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    task = TestTask(1, "1", 100)

    # let somebody have fun when this fails
    merit = RandomMerit()
    assert -100.0 <= merit(time, task, data) <= 100.0
