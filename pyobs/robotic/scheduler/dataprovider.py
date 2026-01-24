from __future__ import annotations
import datetime
from dataclasses import dataclass
from functools import cache
from astroplan import Observer
from astropy.time import Time

from pyobs.robotic.scheduler.observationarchiveevolution import ObservationArchiveEvolution


@dataclass
class TaskSuccess:
    date: Time
    night: Time


class DataProvider:
    """Data provider for Merit classes."""

    def __init__(self, observer: Observer, archive: ObservationArchiveEvolution | None = None):
        self.observer = observer
        self.archive = archive if archive else ObservationArchiveEvolution(observer)

    @cache
    def last_sunset(self, time: Time) -> Time:
        """Returns the time of the last sunset."""

        # get last sunset
        return self.observer.sun_set_time(time, which="previous")

    @cache
    def night(self, time: Time) -> datetime.date:
        """Returns the time of the last sunset."""
        sunset = self.last_sunset(time)
        return sunset.to_datetime().date()  # type: ignore


__all__ = ["DataProvider"]
