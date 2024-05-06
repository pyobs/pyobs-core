import logging
from typing import Tuple, Any, Optional, List, Dict

import numpy as np
import pandas as pd

from pyobs.interfaces import IAcquisition, ITelescope
from pyobs.interfaces import IAutonomous
from pyobs.modules import Module
from pyobs.modules.robotic._pointingseriesiterator import _PointingSeriesIterator

log = logging.getLogger(__name__)


class PointingSeries(Module, IAutonomous):
    """Module for running pointing series."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
            self,
            alt_range: Tuple[float, float] = (30.0, 85.0),
            num_alt: int = 8,
            az_range: Tuple[float, float] = (0.0, 360.0),
            num_az: int = 24,
            dec_range: Tuple[float, float] = (-80.0, 80.0),
            min_moon_dist: float = 15.0,
            finish: int = 90,
            exp_time: float = 1.0,
            acquisition: str = "acquisition",
            telescope: str = "telescope",
            **kwargs: Any,
    ):
        """Initialize a new auto focus system.

        Args:
            alt_range: Range in degrees to use in altitude.
            num_alt: Number of altitude points to create on grid.
            az_range: Range in degrees to use in azimuth.
            num_az: Number of azimuth points to create on grid.
            dec_range: Range in declination in degrees to use.
            min_moon_dist: Minimum moon distance in degrees.
            finish: When this number in percent of points have been finished, terminate mastermind.
            exp_time: Exposure time in secs.
            acquisition: IAcquisition unit to use.
            telescope: ITelescope unit to use.
        """
        Module.__init__(self, **kwargs)

        # store
        self._alt_range = tuple(alt_range)
        self._num_alt = num_alt
        self._az_range = tuple(az_range)
        self._num_az = num_az

        self._acquisition = acquisition
        self._telescope = telescope

        self._pointing_series_iterator = _PointingSeriesIterator(
            self.observer, dec_range,
            finish_percentage=finish,
            min_moon_dist=min_moon_dist
        )

        # if Az range is [0, 360], we got north double, so remove one step
        if self._az_range == (0.0, 360.0):
            self._az_range = (0.0, 360.0 - 360.0 / self._num_az)

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

    async def open(self, **kwargs: Any) -> None:
        await Module.open(self)

        acquisition = await self.proxy(self._acquisition, IAcquisition)
        telescope = await self.proxy(self._telescope, ITelescope)

        self._pointing_series_iterator.set_acquisition(acquisition)
        self._pointing_series_iterator.set_telescope(telescope)

    async def _run_thread(self) -> None:
        """Run a pointing series."""

        pd_grid = self._generate_grid()
        self._pointing_series_iterator.set_grid_points(pd_grid)

        async for acquisition_result in self._pointing_series_iterator:
            if acquisition_result is not None:
                await self._process_acquisition(**acquisition_result)

        # finished
        log.info("Pointing series finished.")

    def _generate_grid(self) -> pd.DataFrame:
        # create grid
        grid: Dict[str, List[Any]] = {"alt": [], "az": [], "done": []}
        for az in np.linspace(self._az_range[0], self._az_range[1], self._num_az):
            for alt in np.linspace(self._alt_range[0], self._alt_range[1], self._num_alt):
                grid["alt"] += [alt]
                grid["az"] += [az]
                grid["done"] += [False]
        # to dataframe
        pd_grid = pd.DataFrame(grid).set_index(["alt", "az"])

        return pd_grid

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
