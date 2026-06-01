from astroplan import Observer
from typing import TYPE_CHECKING
from astropy.coordinates import SkyCoord, AltAz
from astropy.time import Time

from .picker import Picker

if TYPE_CHECKING:
    from pyobs.robotic.scheduler.targets import Target, SiderealTarget


class CsvPicker(Picker):
    """A helper class for picking a target from a list."""

    csv: str
    name_col: str = "name"
    ra_col: str = "ra"
    dec_col: str = "dec"
    frame: str = "icrs"
    min_alt: float | None = None
    max_alt: float | None = None

    async def __call__(self, time: Time) -> Target:
        from pyobs.robotic.scheduler.targets import SiderealTarget

        data = await self.vfs.read_csv(self.csv)
        targets = SkyCoord(ra=data[self.ra_col], dec=data[self.dec_col], frame=self.frame, unit="deg")

        # calculate Alz/Az
        altaz_frame = AltAz(location=self.observer.location, obstime=time)
        altaz = targets.transform_to(altaz_frame)
        data["alt"] = altaz.alt.deg
        data["az"] = altaz.az.deg

        # filter
        d = data
        if self.min_alt is not None:
            d = d[d["alt"] >= self.min_alt]
        if self.max_alt is not None:
            d = d[d["alt"] <= self.max_alt]

        # pick random row
        row = d.sample()
        return SiderealTarget(
            name=row[self.name_col].values[0], ra=row[self.ra_col].values[0], dec=row[self.dec_col].values[0]
        )


__all__ = ["CsvPicker"]
