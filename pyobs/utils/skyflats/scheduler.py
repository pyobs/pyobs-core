from py_expression_eval import Parser
from astropy.time import Time, TimeDelta
import astropy.units as u
from astroplan import Observer
import operator

from pyobs.utils.skyflats.priorities.base import SkyflatPriorities


class ExpTimeEval:
    """Exposure time evaluator for skyflats."""

    def __init__(self, observer: Observer, functions: dict):
        """Initializes a new evaluator.

        Args:
            observer: Observer to use.
            functions: Dict of functions for the different filters.
        """

        # init
        self._observer = observer
        self._time = None
        self._m = None
        self._b = None

        # parse function
        if functions is None:
            functions = {}
        self._functions = {filter_name: Parser().parse(func) for filter_name, func in functions.items()}

    def __call__(self, filter_name: str, binning: int, solalt: float) -> float:
        """Estimate exposure time for given filter

        Args:
            filter_name: Name of filter.
            binning: Used binning in X and Y.
            solalt: Solar altitude.

        Returns:
            Estimated exposure time.
        """
        return self._functions[filter_name].evaluate({'h': solalt}) / binning**2

    def init(self, time: Time):
        """Initialize object with the given time.

        Args:
            time: Start time for all further calculations.
        """

        # store time
        self._time = time

        # get sun now and in 10 minutes
        sun_now = self._observer.sun_altaz(time)
        sun_10min = self._observer.sun_altaz(time + TimeDelta(10 * u.minute))

        # get m, b for calculating sun_alt=m*time+b
        self._b = sun_now.alt.degree
        self._m = (sun_10min.alt.degree - self._b) / (10. * 60.)

    def exp_time(self, filter_name: str, binning: int, time_offset: float) -> float:
        """Estimates exposure time for a given filter and binning at a given time offset from the start time (see init).

        Args:
            filter_name: Name of filter
            binning: Used binning in X and Y
            time_offset: Offset in seconds from start time (see init)

        Returns:
            Estimated exposure time
        """
        return self(filter_name, binning, self._m * time_offset + self._b)

    def duration(self, filter_name: str, binning: int, count: int, start_time: float = 0, readout: int = 1) -> float:
        """Estimates the duration for a given amount of flats in the given filter and binning, starting at the given
        start time.

        Args:
            filter_name: Name of filter
            binning: Used binning in X & Y
            count: Number of flats to take.
            start_time: Time in seconds to start after the time set in init()
            readout: Time in seconds for readout per flat

        Returns:
            Estimated duration in seconds
        """

        # loop through images and add estimated exposure times at their respective start times
        elapsed = start_time
        for i in range(count):
            elapsed += self.exp_time(filter_name, binning, elapsed) + readout

        # we started at start_time, so subtract it again
        return elapsed - start_time


class SchedulerItem:
    """A single item in the flat scheduler"""

    def __init__(self, start: float, end: float, filter_name: str, binning: int):
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

    def __repr__(self):
        """Nice string representation for item"""
        return '%d - %d (%s %dx%d)' % (self.start, self.end, self.filter_name, self.binning, self.binning)


class Scheduler:
    """Scheduler for taking flat fields"""
    def __init__(self, functions: dict, priorities: SkyflatPriorities, observer: Observer, min_exptime: float = 0.5,
                 max_exptime: float = 5, timespan: float = 7200, filter_change: float = 30, count: int = 20):
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
        """
        self._eval = ExpTimeEval(observer, functions)
        self._observer = observer
        self._priorities = priorities
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime
        self._schedules = []
        self._current = 0
        self._timespan = timespan
        self._filter_change = filter_change
        self._count = count

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
        for task, _ in priorities:
            # find possible time
            self._find_slot(schedules, *task)

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

    def _find_slot(self, schedules: list, filter_name: str, binning: int):
        """Find a possible slot for a given filter/binning in the given schedule

        Args:
            schedules: List of existing schedules
            filter_name: Name of filter
            binning: Used binning
        """

        # find first possible start time
        time = 0
        while time < self._timespan:
            # get exposure time
            exp_time_start = self._eval.exp_time(filter_name, binning, time)

            # are we in allowed limit?
            if self._min_exptime <= exp_time_start <= self._max_exptime:
                # seems to fit, get duration
                duration = self._eval.duration(filter_name, binning, self._count, start_time=time)

                # add time for filter change
                duration += self._filter_change

                # get exp time at end
                exp_time_end = self._eval.exp_time(filter_name, binning, time + duration)

                # still in limits?
                if self._min_exptime <= exp_time_end <= self._max_exptime:
                    # check for overlap with existing schedule
                    if not self._overlaps(schedules, time, time + duration):
                        # add schedule and quit
                        schedules.append(SchedulerItem(time, time + duration, filter_name, binning))
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
