from __future__ import annotations

import random
from typing import TYPE_CHECKING, Literal

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from pydantic import PrivateAttr

from pyobs.utils.time import Time

from .picker import Picker

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.robotic.scheduler import DataProvider
    from pyobs.robotic.scheduler.targets import Target


class CsvPicker(Picker):
    """A helper class for picking a target from a list."""

    csv: str
    name_col: str = "name"
    ra_col: str = "ra"
    dec_col: str = "dec"
    frame: str = "icrs"
    ra_unit: Literal["deg", "hour"] = "deg"

    _dataframe: pd.DataFrame | None = PrivateAttr(default=None)
    _coords: SkyCoord | None = PrivateAttr(default=None)

    async def _load(self) -> bool:
        """Load CSV and build coordinate array. Returns False if loading failed."""
        df = await self.vfs.read_csv(self.csv)
        if df is None:
            return False
        ras = df[self.ra_col].values.astype(float)
        if self.ra_unit == "hour":
            df[self.ra_col] *= 15.0
        self._dataframe = df
        self._coords = SkyCoord(ra=ras * u.deg, dec=df[self.dec_col].values.astype(float) * u.deg)
        return True

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> Target | None:
        from pyobs.robotic.scheduler.targets import SiderealTarget

        # load catalogue on first call
        if self._coords is None:
            if not await self._load():
                return None
        if self._coords is None or self._dataframe is None:
            return None

        # start with all candidates
        mask = np.ones(len(self._coords), dtype=np.bool_)

        # apply all target-dependent constraints via filter_skycoord
        for c in sorted((c for c in task.constraints if c.target_dependent), key=lambda c: c.cost):
            mask = mask & await c.filter_skycoord(time, self._coords, data)
            if not mask.any():
                return None

        # pick a random surviving row and create one SiderealTarget
        valid_indices = np.where(mask)[0]
        row = self._dataframe.iloc[int(random.choice(valid_indices))]
        return SiderealTarget(name=str(row[self.name_col]), ra=float(row[self.ra_col]), dec=float(row[self.dec_col]))


__all__ = ["CsvPicker"]
