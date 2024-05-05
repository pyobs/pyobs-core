from __future__ import annotations

import logging
import random
from typing import Tuple, Any, Optional, List, Dict

import astropy
import astropy.units as u
import pandas as pd
from astroplan import Observer
from astropy.coordinates import SkyCoord

from pyobs.interfaces import IAcquisition, ITelescope
from pyobs.utils import exceptions as exc
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class _PointingSeriesIterator:
    def __init__(self,
                 observer: Observer,
                 telescope: ITelescope,
                 acquisition: IAcquisition,
                 dec_range: Tuple[float, float],
                 finish_percentage: float,
                 min_moon_dist: float,
                 grid_points: pd.DataFrame) -> None:

        self._observer = observer
        self._telescope = telescope
        self._acquisition = acquisition

        self._dec_range = dec_range
        self._finish_fraction = 1.0 - finish_percentage / 100.0
        self._min_moon_dist = min_moon_dist

        self._grid_points = grid_points

    def __aiter__(self) -> _PointingSeriesIterator:
        return self

    async def __anext__(self) -> Optional[Dict[str, Any]]:
        if self._is_finished():
            raise StopAsyncIteration()

        todo_coords = self._get_todo_coords()
        log.info("Grid points left to do: %d", len(todo_coords))

        alt, az, radec = self._find_next_point(todo_coords)

        try:
            acquisition_result = await self._acquire_target(radec)
        except (ValueError, exc.RemoteError):
            log.info("Could not acquire target.")
            return None

        self._grid_points.loc[alt, az] = True
        return acquisition_result

    def _is_finished(self) -> bool:
        num_finished_coords: int = sum(self._grid_points["done"].values)
        total_num_coords: int = len(self._grid_points)

        return num_finished_coords/total_num_coords >= self._finish_fraction

    def _get_todo_coords(self) -> List[Tuple[float, float]]:
        return list(self._grid_points[~self._grid_points["done"]].index)

    def _find_next_point(self, todo_coords: List[Tuple[float, float]]) -> Tuple[float, float, astropy.coordinates.SkyCoord]:
        moon = self._observer.moon_altaz(Time.now())
        # try to find a good point
        while True:
            # pick a random index and remove from list
            alt, az = random.sample(todo_coords, 1)[0]
            todo_coords.remove((alt, az))
            altaz = SkyCoord(
                alt=alt * u.deg, az=az * u.deg, frame="altaz", obstime=Time.now(), location=self._observer.location
            )

            # get RA/Dec
            radec = altaz.icrs

            # moon far enough away?
            if altaz.separation(moon).degree >= self._min_moon_dist:
                # yep, are we in declination range?
                if self._dec_range[0] <= radec.dec.degree < self._dec_range[1]:
                    # yep, break here, we found our target
                    break

            # to do list empty?
            if len(todo_coords) == 0:
                # could not find a grid point
                log.info("Could not find a suitable grid point, resetting todo list for next entry...")
                todo_coords = list(self._grid_points.pd_grid.index)
                continue

        log.info("Picked grid point at Alt=%.2f, Az=%.2f (%s).", alt, az, radec.to_string("hmsdms"))
        return alt, az, radec

    async def _acquire_target(self, target: astropy.coordinates.SkyCoord) -> dict[str, Any]:
        await self._telescope.move_radec(float(target.ra.degree), float(target.dec.degree))

        return await self._acquisition.acquire_target()
