import logging
import random
from typing import Tuple, Any, Optional, List, Dict, Union

import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.interfaces import IAcquisition, ITelescope
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
from pyobs.interfaces import IAutonomous
from pyobs.utils.grids.filters import GridFilter
from pyobs.utils.grids.grid import Grid
from pyobs.utils.grids.pipeline import GridPipeline
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingSeries(Module, IAutonomous):
    """Module for running pointing series."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        grid: List[Union[Grid, GridFilter, dict]],
        dec_range: Tuple[float, float] = (-80.0, 80.0),
        min_moon_dist: float = 15.0,
        finish: int = 90,
        exp_time: float = 1.0,
        acquisition: Optional[str] = None,
        telescope: str = "telescope",
        **kwargs: Any,
    ):
        """Initialize a new pointing series.

        Args:
            grid: Grid to use for pointing series.
            dec_range: Range in declination in degrees to use.
            min_moon_dist: Minimum moon distance in degrees.
            finish: When this number in percent of points have been finished, terminate mastermind.
            exp_time: Exposure time in secs.
            acquisition: IAcquisition unit to use.
            telescope: ITelescope unit to use.
        """
        Module.__init__(self, **kwargs)

        # store
        self._grid = GridPipeline(steps=grid)
        self._dec_range = dec_range
        self._min_moon_dist = min_moon_dist
        self._finish = 1.0 - finish / 100.0
        self._exp_time = exp_time
        self._acquisition = acquisition
        self._telescope = telescope

        # add thread func
        self.add_background_task(self._run_thread, False)

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        pass

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        pass

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return True

    async def _run_thread(self) -> None:
        """Run a pointing series."""

        # create grid
        grid: Dict[str, List[Any]] = {"alt": [], "az": [], "done": []}
        for az, alt in self._grid:
            grid["alt"] += [alt]
            grid["az"] += [az]
            grid["done"] += [False]

        # to dataframe
        pd_grid = pd.DataFrame(grid).set_index(["alt", "az"])

        # get acquisition and telescope units
        acquisition = None if self._acquisition is None else await self.proxy(self._acquisition, IAcquisition)
        telescope = await self.proxy(self._telescope, ITelescope)

        # check observer
        if self.observer is None:
            raise ValueError("No observer given.")

        # loop until finished
        while True:
            # get all entries without offset measurements
            todo = list(pd_grid[~pd_grid["done"]].index)
            if len(todo) / len(pd_grid) < self._finish:
                log.info("Finished.")
                break
            log.info("Grid points left to do: %d", len(todo))

            # get moon
            moon = self.observer.moon_altaz(Time.now())

            # try to find a good point
            while True:
                # pick a random index and remove from list
                alt, az = random.sample(todo, 1)[0]
                todo.remove((alt, az))
                altaz = SkyCoord(
                    alt=alt * u.deg, az=az * u.deg, frame="altaz", obstime=Time.now(), location=self.observer.location
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
                if len(todo) == 0:
                    # could not find a grid point
                    log.info("Could not find a suitable grid point, resetting todo list for next entry...")
                    todo = list(pd_grid.index)
                    continue

            # log finding
            log.info("Picked grid point at Alt=%.2f, Az=%.2f (%s).", alt, az, radec.to_string("hmsdms"))

            # acquire target and process result
            try:
                # move telescope
                await telescope.move_radec(float(radec.ra.degree), float(radec.dec.degree))

                # acquire target
                if acquisition is not None:
                    acq = await acquisition.acquire_target()

                    #  process result
                    if acq is not None:
                        await self._process_acquisition(**acq)

            except (ValueError, exc.RemoteError):
                log.info("Could not acquire target.")
                continue

            # finished
            pd_grid.loc[alt, az] = True

        # finished
        log.info("Pointing series finished.")

    async def _process_acquisition(
        self,
        datetime: str,
        ra: float,
        dec: float,
        alt: float,
        az: float,
        off_ra: Optional[float] = None,
        off_dec: Optional[float] = None,
        off_alt: Optional[float] = None,
        off_az: Optional[float] = None,
    ) -> None:
        """Process the result of the acquisition. Either ra_off/dec_off or alt_off/az_off must be given.

        Args:
            datetime: Date and time of observation.
            ra: Right ascension without offsets at destination.
            dec: Declination without offsets at destination.
            alt: Altitude without offsets at destination.
            az: Azimuth without offsets at destination.
            off_ra: Found RA offset.
            off_dec: Found Dec offset.
            off_alt: Found Alt offset.
            off_az: Found Az offset.
        """
        pass


__all__ = ["PointingSeries"]
