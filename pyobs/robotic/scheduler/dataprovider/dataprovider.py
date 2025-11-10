from __future__ import annotations
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING
import astropy
from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimeDelta
import astropy.units as u
from astropy.units import Quantity

if TYPE_CHECKING:
    from pyobs.robotic import Task


@dataclass
class TaskSuccess:
    date: Time
    night: Time


class DataProvider:
    """Data provider for Merit classes."""

    def __init__(self, observer: Observer):
        self.observer = observer

    def reset(self) -> None:
        """Reset data provider."""
        ...

    @cache
    def get_night(self, time: Time) -> Time:
        """Returns the night for the given time."""
        night = Time(f"{time.year}-{time.month:02d}-{time.day:02d} 00:00:00")
        if time.hour < 12:
            night -= TimeDelta(1.0 * u.day)
        return night

    @cache
    def get_task_success_count(self, time: Time, task: Task) -> int:
        """Return the number of successful runs for task."""
        return 0

    @cache
    def get_task_success(self, task: Task, number: int = -1) -> TaskSuccess | None:
        """Return the number of successful runs for task."""
        return None

    def get_distance(self, target: SkyCoord, avoid: SkyCoord) -> Quantity:
        # TODO: figure out something else, since SkyCoord is not hashable, so @cache doesn't work
        return target.separation(avoid)

    @cache
    def get_moon(self, time: Time) -> SkyCoord:
        return astropy.coordinates.get_body("moon", time, self.observer.location)

    @cache
    def get_sun(self, time: Time) -> SkyCoord:
        return astropy.coordinates.get_body("sun", time, self.observer.location)


__all__ = ["DataProvider"]
