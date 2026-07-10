from astropy.coordinates import SkyCoord

from pyobs.utils.time import Time

from .target import Target


class HelioprojectiveTarget(Target):
    tx: float
    ty: float

    @property
    def coord(self) -> SkyCoord:
        return self.coordinates(Time.now())

    def coordinates(self, time: Time) -> SkyCoord:
        from sunpy.coordinates import Helioprojective

        return SkyCoord(
            self.tx,
            self.ty,
            unit="arcsec",
            frame=Helioprojective,
            observer="earth",
            obstime=time,
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.coord})"


__all__ = ["HelioprojectiveTarget"]
