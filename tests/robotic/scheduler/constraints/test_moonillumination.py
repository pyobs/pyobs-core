from __future__ import annotations
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import MoonIlluminationConstraint
from ..task import TestTask
from astropy.time import Time


def test_moonillumination_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    task = TestTask(1, "1", 100)
    constraint = MoonIlluminationConstraint(0.5)

    time = Time("2025-11-05T13:00:00", scale="utc")
    assert constraint(time, task, data) is False

    time = Time("2025-11-12T05:00:00", scale="utc")
    assert constraint(time, task, data) is False

    time = Time("2025-11-12T08:00:00", scale="utc")
    assert constraint(time, task, data) is True

    time = Time("2025-11-13T0:00:00", scale="utc")
    assert constraint(time, task, data) is True
