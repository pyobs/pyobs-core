import logging
import threading
import typing

from pyobs.interfaces import IRunnable, IFlatField
from pyobs import Module
from pyobs.modules import timeout
from pyobs.object import create_object
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.threads import Future
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldScheduler(Module, IRunnable):
    """Run the flat-field scheduler."""

    def __init__(self, flatfield: typing.Union[str, IFlatField], functions: typing.Dict[str, str],
                 priorities: typing.Union[dict, SkyflatPriorities], min_exptime: float = 0.5, max_exptime: float = 5,
                 timespan: float = 7200, filter_change: float = 30, count: int = 20, *args, **kwargs):
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
        Module.__init__(self, *args, **kwargs)

        # store
        self._flatfield = flatfield
        self._count = count

        # abort
        self._abort = threading.Event()

        # priorities
        priorities = create_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(functions, priorities, self.observer, min_exptime=min_exptime,
                                    max_exptime=max_exptime, timespan=timespan, filter_change=filter_change,
                                    count=count)

    def open(self):
        """Open module"""
        Module.open(self)

        # check flat field
        try:
            self.proxy(self._flatfield, IFlatField)
        except ValueError:
            log.warning('Flatfield module does not exist or is not of correct type at the moment.')

    @timeout(7200)
    def run(self, *args, **kwargs):
        """Perform flat-fielding"""
        log.info('Performing flat fielding...')
        self._abort = threading.Event()

        # get flat fielder
        log.info('Getting proxy for flat fielder...')
        flatfield: IFlatField = self.proxy(self._flatfield, IFlatField)

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
            future: Future = flatfield.flat_field(item.filter_name, self._count, item.binning)

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
    def abort(self, *args, **kwargs):
        """Abort current actions."""
        self._abort.set()


__all__ = ['FlatFieldScheduler']
