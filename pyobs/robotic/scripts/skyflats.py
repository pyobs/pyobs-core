from __future__ import annotations
import logging
from typing import Dict, Any, Optional, Union, TYPE_CHECKING

from pyobs.interfaces import IFilters, IBinning, IFlatField, ITelescope, IRoof
from pyobs.robotic.scripts import Script
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class SkyFlats(Script):
    """Script for scheduling and running skyflats using an IFlatField module."""

    def __init__(
        self,
        roof: Union[str, IRoof],
        telescope: Union[str, ITelescope],
        flatfield: Union[str, IFlatField],
        functions: Dict[str, Any],
        priorities: Union[Dict[str, Any], SkyflatPriorities],
        min_exptime: float = 0.5,
        max_exptime: float = 5,
        timespan: float = 7200,
        filter_change: float = 30,
        count: int = 20,
        readout: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Init a new SkyFlats script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            flatfield: FlatFielder to use
            functions: Dict with solalt-exptime functions for all filters/binning
            priorities: SkyflatPriorities object that returns priorities
            min_exptime: Minimum exposure time for flats
            max_exptime: Maximum exposure time for flats
            timespan: Timespan from now that should be scheduled [s]
            filter_change: Time required for filter change [s]
            count: Number of flats to schedule
            readout: Dictionary with readout times (in sec) per binning (as BxB).
        """
        Script.__init__(self, **kwargs)

        # store modules
        self._roof = roof
        self._telescope = telescope
        self._flatfield = flatfield

        # stuff
        self._count = count

        # get archive and priorities
        prio = self.get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(
            functions,
            prio,
            self.observer,
            min_exptime=min_exptime,
            max_exptime=max_exptime,
            timespan=timespan,
            filter_change=filter_change,
            count=count,
            readout=readout,
        )

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
        task_runner: TaskRunner | None = None,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxy for flatfield
        flatfield = await self.comm.proxy(self._flatfield, IFlatField)

        # schedule
        log.info("Scheduling flat-fields...")
        await self._scheduler(Time.now())

        # log schedule
        log.info("Found schedule:")
        for sched in self._scheduler:
            log.info("- %s", sched)

        # total exposure time in ms
        self.exptime_done = 0

        # do flat fields
        item: SchedulerItem
        for item in self._scheduler:
            # do flat fields
            log.info("Performing flat-fields in %s %dx%d...", item.filter_name, *item.binning)
            if isinstance(flatfield, IBinning):
                await flatfield.set_binning(*item.binning)
            if isinstance(flatfield, IFilters):
                await flatfield.set_filter(item.filter_name)
            done, exp_time = await flatfield.flat_field(self._count)
            log.info("Finished flat-fields.")

            # increase exposure time
            self.exptime_done += exp_time

        # finished
        log.info("Finished all scheduled flat-fields.")


__all__ = ["SkyFlats"]
