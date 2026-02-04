from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from pyobs.interfaces import IFilters, IBinning, IFlatField, ITelescope, IRoof
from pyobs.object import get_object
from pyobs.robotic.scripts import Script
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class SkyFlats(Script):
    """Script for scheduling and running skyflats using an IFlatField module."""

    roof: str
    telescope: str
    flatfield: str
    functions: dict[str, Any]
    priorities: dict[str, Any]
    min_exptime: float = 0.5
    max_exptime: float = 5
    timespan: float = 7200
    filter_change: float = 30
    count: int = 20
    readout: dict[str, Any] | None = None

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.

        Returns:
            True if script can run now.
        """

        # get modules
        try:
            roof = await self.__comm(data).proxy(self.roof, IRoof)
            telescope = await self.__comm(data).proxy(self.telescope, ITelescope)
            await self.__comm(data).proxy(self.flatfield, IFlatField)
        except ValueError:
            return False

        # we need an open roof and a working telescope
        if not await roof.is_ready() or not await telescope.is_ready():
            return False

        # seems alright
        return True

    async def run(self, data: TaskData) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get archive and priorities
        prio = get_object(self.priorities, SkyflatPriorities)

        # create scheduler
        scheduler = Scheduler(
            self.functions,
            prio,
            data.observer,
            min_exptime=self.min_exptime,
            max_exptime=self.max_exptime,
            timespan=self.timespan,
            filter_change=self.filter_change,
            count=self.count,
            readout=self.readout,
        )

        # get proxy for flatfield
        flatfield = await self.__comm(data).proxy(self.flatfield, IFlatField)

        # schedule
        log.info("Scheduling flat-fields...")
        await scheduler(Time.now())

        # log schedule
        log.info("Found schedule:")
        for sched in scheduler:
            log.info("- %s", sched)

        # total exposure time in ms
        exptime_done = 0

        # do flat fields
        item: SchedulerItem
        for item in scheduler:
            # do flat fields
            log.info("Performing flat-fields in %s %dx%d...", item.filter_name, *item.binning)
            if isinstance(flatfield, IBinning):
                await flatfield.set_binning(*item.binning)
            if isinstance(flatfield, IFilters):
                await flatfield.set_filter(item.filter_name)
            done, exp_time = await flatfield.flat_field(self.count)
            log.info("Finished flat-fields.")

            # increase exposure time
            exptime_done += exp_time

        # finished
        log.info("Finished all scheduled flat-fields.")


__all__ = ["SkyFlats"]
