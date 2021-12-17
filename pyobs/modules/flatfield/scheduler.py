import asyncio
import logging
from typing import Dict, Any, Union

from pyobs.interfaces import IRunnable
from pyobs.interfaces import IFlatField, IFilters, IBinning
from pyobs.modules import Module
from pyobs.modules import timeout
from pyobs.object import get_object
from pyobs.utils.parallel import event_wait
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldScheduler(Module, IRunnable):
    """Run the flat-field scheduler."""
    __module__ = 'pyobs.modules.flatfield'

    def __init__(self, flatfield: Union[str, IFlatField], functions: Dict[str, str],
                 priorities: Union[Dict[str, Any], SkyflatPriorities], min_exptime: float = 0.5, max_exptime: float = 5,
                 timespan: float = 7200, filter_change: float = 30, count: int = 20, **kwargs: Any):
        """Initialize a new flat field scheduler.

        Args:
            flatfield: Flat field module to use
            functions: Dict with flat functions
            priorities: Class handling priorities
            min_exptime: Minimum exposure time [s]
            max_exptime: Maximum exposure time [s]
            timespan: Time to scheduler after start [s]
            filter_change: Time required for filter change [s]
            count: Number of flats to take per filter/binning
        """
        Module.__init__(self, **kwargs)

        # store
        self._flatfield = flatfield
        self._count = count

        # abort
        self._abort = asyncio.Event()

        # priorities
        prio = get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(functions, prio, self.observer, min_exptime=min_exptime,
                                    max_exptime=max_exptime, timespan=timespan, filter_change=filter_change,
                                    count=count)

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # check flat field
        try:
            await self.proxy(self._flatfield, IFlatField)
        except ValueError:
            log.warning('Flatfield module does not exist or is not of correct type at the moment.')

    @timeout(7200)
    async def run(self, **kwargs: Any) -> None:
        """Perform flat-fielding"""
        log.info('Performing flat fielding...')
        self._abort = asyncio.Event()

        # get flat fielder
        log.info('Getting proxy for flat fielder...')
        flatfield = await self.proxy(self._flatfield, IFlatField)

        # do schedule
        log.info('Scheduling flats...')
        self._scheduler(Time.now())

        # do flat fields
        sched: SchedulerItem
        for item in self._scheduler:
            # aborted?
            if self._abort.is_set():
                log.info('Scheduler aborted.')
                break

            # start
            log.info('Taking %d flats in %s %dx%d...', self._count, item.filter_name, item.binning, item.binning)
            if isinstance(flatfield, IFilters):
                await flatfield.set_filter(item.filter_name)
            if isinstance(flatfield, IBinning):
                await flatfield.set_binning(*item.binning)
            future = asyncio.create_task(flatfield.flat_field(self._count))

            # wait for it
            while not future.done():
                # aborted?
                if self._abort.is_set():
                    log.info('Aborting current flat field...')
                    await flatfield.abort()

                # sleep a little
                await event_wait(self._abort, 1)

        # finished
        log.info('Finished.')

    @timeout(20)
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ['FlatFieldScheduler']
