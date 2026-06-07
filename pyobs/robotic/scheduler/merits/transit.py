from __future__ import annotations

from typing import TYPE_CHECKING, Self

from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from pydantic import Field, PrivateAttr, model_validator

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class TransitMerit(Merit):
    """Merit function for observing transits."""

    # jd0 of first transit
    jd0: float = Field(default=2450000, ge=2400000, le=2499999, json_schema_extra={"decimals": 9})
    # period in days
    period: float = Field(default=1.0, ge=0.01, le=9999, json_schema_extra={"decimals": 9})
    # transit duration in seconds
    duration: int = Field(default=1, ge=1, le=99999)
    # start observation this ingress*duration before 1st contact
    ingress: float = Field(default=0.2, ge=0, le=5)
    # start observation not later than over*duration before 1st contact
    over: float = Field(default=0.0, ge=0, le=5)

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
        return float(Time.now().jd - self.jd0)

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
