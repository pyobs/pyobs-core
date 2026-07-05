import logging
from typing import Any

from astropy.coordinates import SkyCoord

from pyobs.interfaces import AcquisitionResult, IAcquisition, IAutonomous, IPointingRaDec, IPointingSeries
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
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
        if self._observer is None:
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
        log.info("Found %s grid points.", count)

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
            log.info("Finished %s of %s grid points.", finished, count)

        # finished
        log.info("Pointing series finished.")

    async def _process_point(self, coord: SkyCoord) -> bool:
        # acquire target and process result
        try:
            # move telescope
            async with self.proxy(self._telescope, IPointingRaDec) as telescope:
                await telescope.move_radec(float(coord.ra.degree), float(coord.dec.degree))

            # acquire target
            async with self.proxy(self._acquisition, IAcquisition) as acquisition:
                acq = await acquisition.acquire_target()

            #  process result
            await self._process_acquisition(acq)

            # if telescope implements IPointingSeries, let it know
            async with self.safe_proxy(self._telescope, IPointingSeries) as telescope:
                if telescope:
                    await telescope.add_pointing_measurement()

            return True

        except (ValueError, exc.RemoteError):
            log.info("Could not acquire position.")
            return False

    async def _process_acquisition(self, result: AcquisitionResult) -> None:
        pass


__all__ = ["PointingSeries"]
