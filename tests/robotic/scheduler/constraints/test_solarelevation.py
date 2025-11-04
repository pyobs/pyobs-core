from __future__ import annotations
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import SolarElevationConstraint
from ..task import TestTask
from astropy.time import Time


def test_solarelevation_constraint() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    task = TestTask(1, "1", 100)

    constraint = SolarElevationConstraint(-18.0)

    time = Time("2025-11-03T16:00:00", scale="utc")
    assert constraint(time, task, data) is False

    time = Time("2025-11-03T18:30:00", scale="utc")
    assert constraint(time, task, data) is False

    time = Time("2025-11-03T18:35:00", scale="utc")
    assert constraint(time, task, data) is True

    time = Time("2025-11-03T20:00:00", scale="utc")
    assert constraint(time, task, data) is True
