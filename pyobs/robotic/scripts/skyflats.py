import logging
import threading
import typing
from astroplan import Observer

from pyobs import get_object
from pyobs.comm import Comm
from pyobs.interfaces import IMotion, IFlatField, ITelescope, IRoof
from pyobs.robotic.scripts import Script
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class SkyFlats(Script):
    """Script for scheduling and running skyflats using an IFlatField module."""

    def __init__(self, roof: typing.Union[str, IRoof], telescope: typing.Union[str, ITelescope],
                 flatfield: typing.Union[str, IFlatField], functions: dict,
                 priorities: typing.Union[dict, SkyflatPriorities], min_exptime: float = 0.5, max_exptime: float = 5,
                 timespan: float = 7200, filter_change: float = 30, count: int = 20, *args, **kwargs):
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
        """
        Script.__init__(self, *args, **kwargs)

        # store modules
        self._roof = roof
        self._telescope = telescope
        self._flatfield = flatfield

        # stuff
        self._count = count

        # get archive and priorities
        priorities = get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(functions, priorities, self.observer, min_exptime=min_exptime, max_exptime=max_exptime,
                                    timespan=timespan, filter_change=filter_change, count=count)

    def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True if script can run now.
        """

        # get modules
        try:
            roof: IRoof = self.comm.proxy(self._roof, IRoof)
            telescope: ITelescope = self.comm.proxy(self._telescope, ITelescope)
            self.comm.proxy(self._flatfield, IFlatField)
        except ValueError:
            return False

        # we need an open roof and a working telescope
        if not roof.is_ready().wait() or not telescope.is_ready().wait():
            return False

        # seems alright
        return True

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxy for flatfield
        flatfield: IFlatField = self.comm.proxy(self._flatfield, IFlatField)

        # schedule
        log.info('Scheduling flat-fields...')
        self._scheduler(Time.now())

        # log schedule
        log.info('Found schedule:')
        for sched in self._scheduler:
            log.info('- %s', sched)

        # total exposure time in ms
        self.exptime_done = 0

        # do flat fields
        item: SchedulerItem
        for item in self._scheduler:
            self._check_abort(abort_event)

            # do flat fields
            log.info('Performing flat-fields in %s %dx%d...', item.filter_name, item.binning, item.binning)
            done, exp_time = flatfield.flat_field(item.filter_name, self._count, item.binning).wait()
            log.info('Finished flat-fields.')

            # increase exposure time
            self.exptime_done += exp_time

        # finished
        log.info('Finished all scheduled flat-fields.')


__all__ = ['SkyFlats']
