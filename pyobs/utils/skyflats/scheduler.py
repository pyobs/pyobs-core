import logging
from astroplan import Observer
import operator

from .exptimeeval import ExpTimeEval
from .priorities import SkyflatPriorities
from ..time import Time


log = logging.getLogger(__name__)


class SchedulerItem:
    """A single item in the flat scheduler"""

    def __init__(self, start: float, end: float, filter_name: str, binning: int, priority: float):
        """Initializes a new scheduler item

        Args:
            start: Start time in seconds
            end: End time in seconds
            filter_name: Name of filter
            binning: Used binning in X and Y
        """
        self.start = start
        self.end = end
        self.filter_name = filter_name
        self.binning = binning
        self.priority = priority

    def __repr__(self):
        """Nice string representation for item"""
        return '%d - %d (%s %dx%d): %.2f' % (self.start, self.end, self.filter_name,
                                             self.binning, self.binning, self.priority)


class Scheduler:
    """Scheduler for taking flat fields"""
    __module__ = 'pyobs.utils.skyflats'

    def __init__(self, functions: dict, priorities: SkyflatPriorities, observer: Observer, min_exptime: float = 0.5,
                 max_exptime: float = 5, timespan: float = 7200, filter_change: float = 30, count: int = 20,
                 combine_binnings: bool = True, readout: dict = None):
        """Initializes a new scheduler for taking flat fields

        Args:
            functions: Flat field functions
            priorities: Class handling priorities
            observer: Observer to use
            min_exptime: Minimum exposure time for flats
            max_exptime: Maximum exposure time for flats
            timespan: Timespan from now that should be scheduled [s]
            filter_change: Time required for filter change [s]
            count: Number of flats to schedule
            combine_binnings: Whether different binnings use the same functions.
            readout: Dictionary with readout times (in sec) per binning (as BxB).
        """
        self._eval = ExpTimeEval(observer, functions, combine_binnings=combine_binnings)
        self._observer = observer
        self._priorities = priorities
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime
        self._schedules = []
        self._current = 0
        self._timespan = timespan
        self._filter_change = filter_change
        self._count = count
        self._readout = {} if readout is None else readout

    def __call__(self, time: Time):
        """Calculate schedule starting at given time

        Args:
            time: Time to start schedule at
        """

        # init evaluator
        self._eval.init(time)

        # sort filters by priority
        priorities = sorted(self._priorities().items(), key=operator.itemgetter(1), reverse=True)

        # place them
        schedules = []
        for task, priority in priorities:
            # find possible time
            self._find_slot(schedules, *task, priority)

        # sort by start time
        self._schedules = sorted(schedules, key=lambda x: x.start)

    def __iter__(self):
        """Iterator for scheduler items"""
        self._current = 0
        return self

    def __next__(self) -> SchedulerItem:
        """Iterate over scheduler items"""
        if self._current < len(self._schedules):
            item = self._schedules[self._current]
            self._current += 1
            return item
        else:
            raise StopIteration

    def _find_slot(self, schedules: list, filter_name: str, binning: int, priority: float):
        """Find a possible slot for a given filter/binning in the given schedule

        Args:
            schedules: List of existing schedules
            filter_name: Name of filter
            binning: Used binning
        """

        # get readout time
        sbin = '%dx%d' % (binning, binning)
        readout = self._readout[sbin] if sbin in self._readout else 0.

        # find first possible start time
        time = 0
        while time < self._timespan:
            # get exposure time
            exp_time_start = self._eval.exp_time(filter_name, binning, time)

            # are we in allowed limit?
            if self._min_exptime <= exp_time_start <= self._max_exptime:
                # seems to fit, get duration
                duration = self._eval.duration(filter_name, binning, self._count, start_time=time, readout=readout)

                # add time for filter change
                duration += self._filter_change

                # get exp time at end
                exp_time_end = self._eval.exp_time(filter_name, binning, time + duration)

                # still in limits?
                if self._min_exptime <= exp_time_end <= self._max_exptime:
                    # check for overlap with existing schedule
                    if not self._overlaps(schedules, time, time + duration):
                        # add schedule and quit
                        schedules.append(SchedulerItem(time, time + duration, filter_name, binning, priority))
                        return

            # next step
            time += 10

        # being here means we didn't find any
        return

    def _overlaps(self, schedules: list, start: float, end: float) -> bool:
        """Checks, whether a new scheduler item would overlap an existing item

        Args:
            schedules: List of existing scheduler items
            start: Start time of new item
            end: End time of new item

        Returns:
            Whether it overlaps
        """

        # loop all scheduler items
        item: SchedulerItem
        for item in schedules:
            # does it overlap?
            if (start < item.end and end > item.start) or (item.start < end and item.end > start):
                return True

        # no overlap found
        return False


__all__ = ['SchedulerItem', 'Scheduler']
