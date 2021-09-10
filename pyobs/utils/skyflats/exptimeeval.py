import itertools
import re
from typing import Dict, Optional, Union, List
from astroplan import Observer
from astropy.time import TimeDelta
from py_expression_eval import Parser
import logging
import astropy.units as u

from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class ExpTimeEval:
    """Exposure time evaluator for skyflats."""

    def __init__(self, observer: Observer, functions: Union[str, Dict[str, Union[str, Dict[str, str]]]]):
        """Initializes a new evaluator.

        Args:
            observer: Observer to use.
            functions: Dict of functions for the different filters/binnings.
                Three possible formats:
                1. Just a string with a function, e.g. 'exp(-0.9*(h+3.9))', completely ignoring binning and filter.
                2. Dictionary on filter or binning like
                   {'1x1': 'exp(-0.9*(h+3.9))'}
                   or
                   {'clear': 'exp(-0.9*(h+3.9))'}
                   If a binning is given, filters are ignored, and vice versa. Binnings need to be given as NxN.
                3. Nested dictionary with binning and filter like
                   {'1x1': {'clear': 'exp(-0.9*(h+3.9))'}}
                   In this structure, binning must be the first layer, followed by filter.
        """

        # init
        self._observer = observer
        self._time = None
        self._m = None
        self._b = None

        # get parser and init functions dict
        p = Parser()
        self._functions: Dict[(Optional[str], Optional[str])] = {}

        # so, what format is the functions dict?
        if isinstance(functions, str):
            # single function
            self._functions[None, None] = p.parse(functions)
            log.info('Found a single flatfield function for all binnings and filters.')

        else:
            # check, whether keys are binnings or filters
            is_binning = [re.match('[0-9]+x[0-9]+', k) is not None for k in functions.keys()]
            if any(is_binning) and not all(is_binning):
                raise ValueError('Inconsistent configuration: first layer is neither all binnings nor all filters. ')

            # if all entries in is_binning are True, first layer is binnings
            if all(is_binning):
                # 1st level is binnings, is next level strings or another dict?
                is_str = [isinstance(f, str) for f in functions.values()]
                if any(is_str) and not all(is_str):
                    raise ValueError('Inconsistent configuration: second layer is neither all str nor all dicts.')

                # filters or not?
                if all(is_str):
                    # all strings, so we don't have filters
                    self._functions = {(b, None): p.parse(func) for b, func in functions.items()}

                else:
                    # need to go a level deeper
                    for b, tmp in functions.items():
                        for f, func in tmp.items():
                            self._functions[b, f] = p.parse(func)

            else:
                # 1st level is filters, second level must be strings!
                is_str = [isinstance(f, str) for f in functions.values()]
                if not all(is_str):
                    raise ValueError('Inconsistent configuration: second level must be functions.')

                # parse
                self._functions = {(None, f): p.parse(func) for f, func in functions.items()}

    def _keys(self, i):
        keys = list(set([k[i] for k in self._functions.keys()]))
        if None in keys:
            keys.remove(None)
        return sorted(keys)

    @property
    def binnings(self) -> List[str]:
        """Return list of binnings."""
        return self._keys(0)

    @property
    def filters(self) -> List[str]:
        """Return list of filters."""
        return self._keys(1)

    def __call__(self, solalt: float, binning: int = None, filter_name: str = None) -> float:
        """Estimate exposure time for given filter

        Args:
            solalt: Solar altitude.
            binning: Used binning in X and Y.
            filter_name: Name of filter.

        Returns:
            Estimated exposure time.
        """

        # build binning string (if given)
        got_binnings = len(self.binnings) > 0
        sbin = '%dx%d' % (binning, binning) if got_binnings and binning is not None else None

        # if we got no filters, ignore filter_name, if given
        if len(self.filters) == 0:
            filter_name = None

        # get function and evaluate it
        exptime = self._functions[sbin, filter_name].evaluate({'h': solalt})

        # need to scale with exp time?
        return exptime/binning**2 if not got_binnings and binning is not None else exptime

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

    def duration(self, filter_name: str, binning: int, count: int, start_time: float = 0, readout: float = 0) -> float:
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