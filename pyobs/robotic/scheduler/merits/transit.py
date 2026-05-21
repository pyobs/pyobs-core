from __future__ import annotations
from astropy.coordinates import SkyCoord, EarthLocation
from typing import TYPE_CHECKING
from astropy.time import Time
from astropydantic import AstroPydanticTime  # type: ignore

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
    # step of transits to observe, 1=all
    step: int = 1
    # start observation this ingress*duration before 1st contact
    ingress: float = 0.2
    # start observation not later than over*duration before 1st contact
    over: float = 0.0

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        if task.target is None:
            return 0.0

        # current phase
        phi = self.phase_for_jd(task.target.coordinates(time), data.observer.location, time.jd)

        # convert parameters to phase space
        duration = self.duration / 86400.0 / self.period
        ingress = self.ingress / 86400.0 / self.period
        over = self.over / 86400.0 / self.period

        # check
        return float(1.0 - duration / 2.0 - ingress <= phi <= 1.0 - duration / 2.0 - over)

    def phase_for_jd(self, target: SkyCoord, location: EarthLocation, jd: float) -> float:
        hjd = self.jd_to_hjd(target, location, jd)
        phi = ((hjd - self.jd0) % self.period) / self.period
        return phi if phi >= 0 else phi + 1.0

    @staticmethod
    def jd_to_hjd(target: SkyCoord, location: EarthLocation, jd: float) -> float:
        t = Time(jd, format="jd", scale="utc")
        t_bjd = t.light_travel_time(target, kind="barycentric", location=location)
        bjd = (t + t_bjd).tdb.jd
        return float(bjd)


__all__ = ["TransitMerit"]
