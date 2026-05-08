import asyncio
from typing import Any

import pandas as pd
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

        self._data: pd.DataFrame = pd.DataFrame()
        self._targets: SkyCoord = SkyCoord(0, 0, frame=frame, unit="deg")
        asyncio.create_task(self._load_csv())

    async def _load_csv(self):
        self._data = await self.vfs.read_csv(self._csv)
        self._targets = SkyCoord(
            ra=self._data[self._ra_col], dec=self._data[self._dec_col], frame=self._frame, unit="deg"
        )

    def __call__(self, min_alt: float | None = None, max_alt: float | None = None) -> tuple[str, SkyCoord]:
        # calculate Alz/Az
        altaz_frame = AltAz(location=self.observer.location, obstime=Time.now())
        altaz = self._targets.transform_to(altaz_frame)
        self._data["alt"] = altaz.alt.deg
        self._data["az"] = altaz.az.deg

        # filter
        data = self._data
        if min_alt is not None:
            data = data[data["alt"] >= min_alt]
        if max_alt is not None:
            data = data[data["alt"] <= max_alt]

        # pick random row
        row = data.sample()
        return row[self._name_col].values[0], SkyCoord(
            row[self._ra_col].values[0], row[self._dec_col].values[0], frame=self._frame, unit="deg"
        )


__all__ = ["TargetPicker"]
