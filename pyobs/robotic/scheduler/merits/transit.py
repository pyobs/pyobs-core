from __future__ import annotations
from astropy.coordinates import SkyCoord, EarthLocation
from pydantic import model_validator, PrivateAttr
from typing import TYPE_CHECKING, Self
from astropy.time import Time

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class TransitMerit(Merit):
    """Merit function for observing transits."""

    # jd0 of first transit
    jd0: float
    # period in days
    period: float
    # transit duration in seconds
    duration: float
    # start observation this ingress*duration before 1st contact
    ingress: float = 0.2
    # start observation not later than over*duration before 1st contact
    over: float = 0.0

    _duration: float = PrivateAttr(default=0.0)
    _ingress: float = PrivateAttr(default=0.0)
    _over: float = PrivateAttr(default=0.0)

    @model_validator(mode="after")
    def calculate_derived(self) -> Self:
        self._duration = self.duration / 86400.0 / self.period
        self._ingress = self.ingress * self.duration / 86400.0 / self.period
        self._over = self.over * self.duration / 86400.0 / self.period
        return self

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        if task.target is None:
            return 0.0

        # current phase
        phi = self.phase_for_jd(task.target.coordinates(time), data.observer.location, time)

        # check
        return float(1.0 - self._duration / 2.0 - self._ingress <= phi <= 1.0 - self._duration / 2.0 - self._over)

    def days_since_jd0(self) -> float:
        return Time.now().jd - self.jd0

    def periods_since_jd0(self) -> int:
        p = self.days_since_jd0() / self.period
        return round(p)

    def phase_for_jd(self, target: SkyCoord, location: EarthLocation, time: Time) -> float:
        hjd = self.jd_to_hjd(target, location, time)
        phi = ((hjd - self.jd0) % self.period) / self.period
        return phi if phi >= 0 else phi + 1.0

    @staticmethod
    def jd_to_hjd(target: SkyCoord, location: EarthLocation, time: Time) -> float:
        t_bjd = time.light_travel_time(target, kind="barycentric", location=location)
        bjd = (time + t_bjd).tdb.jd
        return float(bjd)


__all__ = ["TransitMerit"]
