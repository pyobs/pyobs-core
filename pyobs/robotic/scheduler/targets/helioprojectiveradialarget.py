from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time

from .target import Target


class HelioprojectiveRadialTarget(Target):
    psi: float
    delta: float

    @property
    def coord(self) -> SkyCoord:
        return self.coordinates(Time.now())

    def coordinates(self, time: Time) -> SkyCoord:
        from sunpy.coordinates import HelioprojectiveRadial  # type: ignore

        return SkyCoord(
            self.psi,
            self.delta,
            unit="deg",
            frame=HelioprojectiveRadial,
            observer="earth",
            obstime=time,
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.coord})"


__all__ = ["HelioprojectiveRadialTarget"]
