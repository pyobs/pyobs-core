from __future__ import annotations

from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time, TimeDelta
import astropy.units as u

from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import TimeWindowMerit
from ..task import TestTask


def test_timewindow_merit() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    time = Time.now()
    time2 = time + TimeDelta(1.0 * u.hour)
    min5 = TimeDelta(5.0 * u.minute)
    task = TestTask(1, "1", 100)

    merit = TimeWindowMerit([{"start": time - min5, "end": time + min5}, {"start": time2 - min5, "end": time2 + min5}])
    assert merit(time, task, data) == 1.0
    assert merit(time + min5 + min5, task, data) == 0.0

    merit = TimeWindowMerit(
        [{"start": time - min5, "end": time + min5}, {"start": time2 - min5, "end": time2 + min5}], inverse=True
    )
    assert merit(time, task, data) == 0.0
    assert merit(time + min5 + min5, task, data) == 1.0
