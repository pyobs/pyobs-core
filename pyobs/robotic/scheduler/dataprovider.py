from __future__ import annotations

import datetime
from dataclasses import dataclass
from functools import cache

import astropy.coordinates
from astroplan import Observer
from astropy.coordinates import SkyCoord

from pyobs.robotic.scheduler.observationarchiveevolution import (
    ObservationArchiveEvolution,
)
from pyobs.utils.time import Time


@dataclass
class TaskSuccess:
    date: Time
    night: Time


class DataProvider:
    """Data provider for Merit classes.

    The ``@cache``d methods below are only safe to call from a single thread at a time -- they're
    used exclusively from within the scheduler's dedicated single-worker executor
    (`pyobs.robotic.scheduler._executor.run_cpu_bound`), never concurrently from the caller's main
    event loop. A new `DataProvider` is created per `schedule()` call, so cache lifetime is bounded
    to one schedule computation and never leaks stale values across runs.
    """

    def __init__(self, observer: Observer, archive: ObservationArchiveEvolution | None = None):
        self.observer = observer
        self.archive = archive if archive else ObservationArchiveEvolution(observer)

    @cache
    def last_sunset(self, time: Time) -> Time:
        """Returns the time of the last sunset."""

        # get last sunset
        return Time(self.observer.sun_set_time(time, which="previous"))

    @cache
    def last_sunrise(self, time: Time) -> Time:
        """Returns the time of the last sunrise."""

        # get last sunset
        return Time(self.observer.sun_rise_time(time, which="previous"))

    @cache
    def night(self, time: Time) -> datetime.date:
        """Returns the time of the last sunset."""
        sunset = self.last_sunset(time)
        return sunset.to_datetime().date()

    @cache
    def sun(self, time: Time) -> SkyCoord:
        """Returns the Sun's coordinates at the given time."""
        return astropy.coordinates.get_sun(time)

    @cache
    def sun_altaz(self, time: Time) -> SkyCoord:
        """Returns the Sun's AltAz coordinates at the given time, as seen by the observer."""
        return self.observer.sun_altaz(time)

    @cache
    def moon(self, time: Time) -> SkyCoord:
        """Returns the Moon's coordinates at the given time."""
        return astropy.coordinates.get_body("moon", time)

    @cache
    def moon_illumination(self, time: Time) -> float:
        """Returns the Moon's illumination fraction at the given time."""
        return float(self.observer.moon_illumination(time))


__all__ = ["DataProvider"]
