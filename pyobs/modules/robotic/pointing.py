import logging
from typing import Any
from astropy.coordinates import SkyCoord

from pyobs.interfaces import IAcquisition, IPointingRaDec
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
from pyobs.interfaces import IAutonomous
from pyobs.utils.grids.filters import GridFilter
from pyobs.utils.grids.grid import Grid
from pyobs.utils.grids.gridnode import GridNode
from pyobs.utils.grids.pipeline import GridPipeline

log = logging.getLogger(__name__)


class PointingSeries(Module, IAutonomous):
    """Module for running pointing series."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        grid: list[Grid | GridFilter | dict[str, Any]],
        finish: int = 90,
        acquisition: str | None = None,
        telescope: str = "telescope",
        **kwargs: Any,
    ):
        """Initialize a new pointing series.

        Args:
            grid: Grid to use for pointing series.
            finish: When this number in percent of points have been finished, terminate mastermind.
            acquisition: IAcquisition unit to use.
            telescope: ITelescope unit to use.
        """
        Module.__init__(self, **kwargs)

        # store
        self._grid = grid
        self._finish = 1.0 - finish / 100.0
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

        # check observer
        if self.observer is None:
            raise ValueError("No observer given.")

        try:
            await self._run_pointing_series()
        except:
            log.exception("Error running series.")
            raise

    async def _run_pointing_series(self) -> None:
        # get grid and get count
        grid = self.get_object(GridPipeline, GridNode, steps=self._grid)
        count = len([coord for coord in grid])
        log.info(f"Found {count} grid points.")

        # iterate over all grid points
        grid = self.get_object(GridPipeline, GridNode, steps=self._grid)
        finished = 0
        for coord in grid:
            if not isinstance(coord, SkyCoord):
                raise ValueError("Coordinate given is not a SkyCoord.")

            # log finding
            grid.log_last()

            # perform acquisition on given coordinates
            if not await self._process_point(coord):
                grid.append_last()
                continue

            # got it
            finished += 1
            log.info(f"Finished {finished} of {count} grid points.")

        # finished
        log.info("Pointing series finished.")

    async def _process_point(self, coord: SkyCoord) -> bool:
        # get acquisition and telescope units
        acquisition = await self.proxy(self._acquisition, IAcquisition)
        telescope = await self.proxy(self._telescope, IPointingRaDec)

        # acquire target and process result
        try:
            # move telescope
            await telescope.move_radec(float(coord.ra.degree), float(coord.dec.degree))

            # acquire target
            acq = await acquisition.acquire_target()

            #  process result
            await self._process_acquisition(**acq)
            return True

        except (ValueError, exc.RemoteError):
            log.info("Could not acquire position.")
            return False

    async def _process_acquisition(
        self,
        datetime: str,
        ra: float,
        dec: float,
        alt: float,
        az: float,
        off_ra: float | None = None,
        off_dec: float | None = None,
        off_alt: float | None = None,
        off_az: float | None = None,
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
