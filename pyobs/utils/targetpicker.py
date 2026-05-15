from typing import Any
from astropy.coordinates import SkyCoord, AltAz
from astropy.time import Time

from pyobs.object import Object


class TargetPicker(Object):
    """A helper class for picking a target from a list."""

    def __init__(
        self,
        csv: str,
        name_col: str = "name",
        ra_col: str = "ra",
        dec_col: str = "dec",
        frame: str = "icrs",
        min_alt: float | None = None,
        max_alt: float | None = None,
        **kwargs: Any,
    ):
        """Create a new target picker.

        Args:
            name: Name of item
            data: Data for this item or None.
        """
        Object.__init__(self, **kwargs)

        self._csv = csv
        self._name_col = name_col
        self._ra_col = ra_col
        self._dec_col = dec_col
        self._frame = frame
        self._min_alt = min_alt
        self._max_alt = max_alt

    async def __call__(self) -> tuple[str, SkyCoord]:
        data = await self._vfs.read_csv(self._csv)
        targets = SkyCoord(ra=data[self._ra_col], dec=data[self._dec_col], frame=self._frame, unit="deg")

        # calculate Alz/Az
        altaz_frame = AltAz(location=self._observer.location, obstime=Time.now())
        altaz = targets.transform_to(altaz_frame)
        data["alt"] = altaz.alt.deg
        data["az"] = altaz.az.deg

        # filter
        d = data
        if self._min_alt is not None:
            d = d[d["alt"] >= self._min_alt]
        if self._max_alt is not None:
            d = d[d["alt"] <= self._max_alt]

        # pick random row
        row = d.sample()
        return row[self._name_col].values[0], SkyCoord(
            row[self._ra_col].values[0], row[self._dec_col].values[0], frame=self._frame, unit="deg"
        )


__all__ = ["TargetPicker"]
