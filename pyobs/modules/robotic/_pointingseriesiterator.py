from __future__ import annotations

import logging
import random
from collections.abc import Iterator
from copy import copy
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


class _LoopedRandomIterator(Iterator[Any]):
    def __init__(self, data: List[Any]) -> None:
        self._data = copy(data)
        self._todo = copy(data)

    def __iter__(self) -> _LoopedRandomIterator:
        return self

    def __next__(self) -> Any:
        if len(self._todo) == 0:
            self._todo = copy(self._data)

        item = random.sample(self._todo, 1)[0]
        self._todo.remove(item)

        return item


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

    def _find_next_point(self, todo_coords: List[Tuple[float, float]]) -> Tuple[float, float, astropy.coordinates.SkyCoord]:  # type: ignore
        moon = self._observer.moon_altaz(Time.now())

        for alt, az in _LoopedRandomIterator(todo_coords):
            altaz = SkyCoord(
                alt=alt * u.deg, az=az * u.deg, frame="altaz", obstime=Time.now(), location=self._observer.location
            )
            radec = altaz.icrs

            if self._is_valid_target(altaz, radec, moon):
                log.info("Picked grid point at Alt=%.2f, Az=%.2f (%s).", alt, az, radec.to_string("hmsdms"))
                return alt, az, radec

    def _is_valid_target(self, altaz_coords: SkyCoord, radec_coords: SkyCoord, moon: SkyCoord) -> bool:
        moon_separation_condition: bool = altaz_coords.separation(moon).degree >= self._min_moon_dist
        dec_range_condition: bool = self._dec_range[0] <= radec_coords.dec.degree < self._dec_range[1]

        return moon_separation_condition and dec_range_condition

    async def _acquire_target(self, target: SkyCoord) -> dict[str, Any]:
        await self._telescope.move_radec(float(target.ra.degree), float(target.dec.degree))

        return await self._acquisition.acquire_target()
