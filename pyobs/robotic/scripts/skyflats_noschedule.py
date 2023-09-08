from __future__ import annotations
import logging
from typing import Dict, Any, Optional, Union, TYPE_CHECKING, Tuple

from pyobs.interfaces import IFilters, IBinning, IFlatField, ITelescope, IRoof
from pyobs.robotic.scripts import Script

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class SkyFlats(Script):
    """Script for scheduling and running skyflats using an IFlatField module."""

    def __init__(
        self,
        roof: Union[str, IRoof],
        telescope: Union[str, ITelescope],
        camera: Union[str, ICamera],
        flatfield: Union[str, IFlatField],
        binning: Tuple[int, int],
        filter_name: Union[str, IFilters],
        count: int = 20,
        **kwargs: Any,
    ):
        """Init a new SkyFlats script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            camera: name of ICamera that takes the image
            flatfield: FlatFielder to use
            count: Number of flats to schedule
        """
        if "configuration" not in kwargs:
            kwargs["configuration"] = {}
        Script.__init__(self, **kwargs)

        # store modules
        self._roof = roof
        self._telescope = telescope
        self._flatfield = flatfield

        # stuff
        self._count = count
        self._camera = camera
        self._binning = binning
        self._filter_name = filter_name

    async def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True if script can run now.
        """

        # get modules
        try:
            roof = await self.comm.proxy(self._roof, IRoof)
            telescope = await self.comm.proxy(self._telescope, ITelescope)
            await self.comm.proxy(self._flatfield, IFlatField)
        except ValueError:
            return False

        # we need an open roof and a working telescope
        if not await roof.is_ready() or not await telescope.is_ready():
            return False

        # seems alright
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        log.info("Starting a series of %s skyflats with %s..." % (self._count, self._camera))
        # get proxy for flatfield
        flatfield = await self.comm.proxy(self._flatfield, IFlatField)

        # total exposure time in ms
        self.exptime_done = 0

        if isinstance(flatfield, IBinning):
            await flatfield.set_binning(*self._binning)
        if isinstance(flatfield, IFilters):
            await flatfield.set_filter(self._filter_name)
        done, exp_time = await flatfield.flat_field(self._count)
        log.info("Finished flat-fields.")

        # increase exposure time
        self.exptime_done += exp_time

        log.info("Finished series of %s skyflats with %s." % (self._count, self._camera))


__all__ = ["SkyFlats"]
