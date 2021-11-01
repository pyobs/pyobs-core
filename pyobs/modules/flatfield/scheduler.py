import logging
import threading
from typing import Dict, Any, Union

from pyobs.interfaces import IRunnable
from pyobs.interfaces.proxies import IFlatFieldProxy, IFiltersProxy, IBinningProxy
from pyobs.modules import Module
from pyobs.modules import timeout
from pyobs.object import get_object
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldScheduler(Module, IRunnable):
    """Run the flat-field scheduler."""
    __module__ = 'pyobs.modules.flatfield'

    def __init__(self, flatfield: Union[str, IFlatFieldProxy], functions: Dict[str, str],
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
        self._abort = threading.Event()

        # priorities
        prio = get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(functions, prio, self.observer, min_exptime=min_exptime,
                                    max_exptime=max_exptime, timespan=timespan, filter_change=filter_change,
                                    count=count)

    def open(self) -> None:
        """Open module"""
        Module.open(self)

        # check flat field
        try:
            self.proxy(self._flatfield, IFlatFieldProxy)
        except ValueError:
            log.warning('Flatfield module does not exist or is not of correct type at the moment.')

    @timeout(7200)
    def run(self, **kwargs: Any) -> None:
        """Perform flat-fielding"""
        log.info('Performing flat fielding...')
        self._abort = threading.Event()

        # get flat fielder
        log.info('Getting proxy for flat fielder...')
        flatfield: IFlatFieldProxy = self.proxy(self._flatfield, IFlatFieldProxy)

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
            if isinstance(flatfield, IFiltersProxy):
                flatfield.set_filter(item.filter_name)
            if isinstance(flatfield, IBinningProxy):
                flatfield.set_binning(*item.binning)
            future = flatfield.flat_field(self._count)

            # wait for it
            while not future.is_done():
                # aborted?
                if self._abort.is_set():
                    log.info('Aborting current flat field...')
                    flatfield.abort().wait()

                # sleep a little
                self._abort.wait(1)

        # finished
        log.info('Finished.')

    @timeout(20)
    def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ['FlatFieldScheduler']
