import logging
import threading
import time
import typing
from astroplan import Observer

from pyobs import get_object
from pyobs.comm import Comm
from pyobs.interfaces import IMotion, IFlatField, ITelescope, IRoof
from pyobs.utils.archive import Archive
from pyobs.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.utils.skyflats.scheduler import Scheduler, SchedulerItem
from pyobs.utils.threads.checkabort import check_abort
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class SkyFlats:
    """Script for scheduling and running skyflats using an IFlatField module."""

    def __init__(self, roof: typing.Union[str, IRoof], telescope: typing.Union[str, ITelescope],
                 flatfield: typing.Union[str, IFlatField], functions: dict,
                 priorities: typing.Union[dict, SkyflatPriorities], comm: Comm, observer: Observer,
                 min_exptime: float = 0.5, max_exptime: float = 5, timespan: float = 7200, filter_change: float = 30,
                 count: int = 20, *args, **kwargs):
        """Init a new SkyFlats script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            flatfield: FlatFielder to use
            functions: Dict with solalt-exptime functions for all filters/binning
            priorities: SkyflatPriorities object that returns priorities
            comm: Comm object to use
            observer: Observer to use
            min_exptime: Minimum exposure time for flats
            max_exptime: Maximum exposure time for flats
            timespan: Timespan from now that should be scheduled [s]
            filter_change: Time required for filter change [s]
            count: Number of flats to schedule
        """

        # store modules
        self._roof = roof
        self._telescope = telescope
        self._flatfield = flatfield

        # stuff
        self._observer = observer
        self._comm = comm
        self._count = count

        # get archive and priorities
        priorities = get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(functions, priorities, observer, min_exptime=min_exptime, max_exptime=max_exptime,
                                    timespan=timespan, filter_change=filter_change, count=count)

    def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True if script can run now.
        """

        # get modules
        try:
            roof: IRoof = self._comm.proxy(self._roof, IRoof)
            telescope: ITelescope = self._comm.proxy(self._telescope, ITelescope)
            self._comm.proxy(self._flatfield, IFlatField)
        except ValueError:
            return False

        # we need an open roof and a working telescope
        if roof.get_motion_status().wait() not in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING] or \
                telescope.get_motion_status().wait() != IMotion.Status.IDLE:
            return False

        # seems alright
        return True

    def __call__(self, abort_event: threading.Event) -> int:
        """Run configuration.

        Args:
            abort_event: Event to abort run.

        Returns:
            Total exposure time in ms.
        """

        # get proxy for flatfield
        flatfield: IFlatField = self._comm.proxy(self._flatfield, IFlatField)

        # schedule
        self._scheduler(Time.now())

        # measure time
        start_time = time.time()

        # do flat fields
        item: SchedulerItem
        for item in self._scheduler:
            # check for abort
            check_abort(abort_event)

            # do flat fields
            log.info('Performing flat-fields in %s %dx%d...', item.filter_name, item.binning, item.binning)
            flatfield.flat_field(item.filter_name, self._count, item.binning).wait()

        # return elapsed time
        return int((time.time() - start_time) * 1000)


__all__ = ['SkyFlats']
