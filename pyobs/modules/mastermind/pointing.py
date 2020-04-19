import logging
import random
from threading import Event

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs import PyObsModule
from pyobs.interfaces import IAcquisition, IPointingSeries, IAbortable
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingSeries(PyObsModule, IPointingSeries, IAbortable):
    """Module for running pointing series."""

    def __init__(self, min_alt: int = 30, max_alt: int = 85, finish: int = 90, exp_time: int = 1000,
                 acquisition: str = 'acquisition', *args, **kwargs):
        """Initialize a new auto focus system.

        Args:
            min_alt: Mininum altitude to use.
            max_alt: Maximum altidude to use.
            finish: When this number in percent of points have been finished, terminate mastermind.
            exp_time: Exposure time in ms.
            acquisition: IAcquisition unit to use.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store
        self._min_alt = min_alt
        self._max_alt = max_alt
        self._finish = 1. - finish / 100.
        self._exp_time = exp_time
        self._acquisition = acquisition
        self._abort = Event()

    def close(self):
        """Close module."""
        PyObsModule.close(self)
        self._abort.set()

    def pointing_series(self, num_alt: int = 8, num_az: int = 24, *args, **kwargs):
        """Reduces all data within a given range of time.

        Args:
            num_alt: Number of altitude points to create on grid.
            num_az: Number of azimuth points to create on grid.
        """

        # create grid
        grid = {'alt': [], 'az': [], 'done': []}
        for az in np.linspace(0, 360 - 360 / num_az, num_az):
            for alt in np.linspace(self._min_alt, self._max_alt, num_alt):
                grid['alt'] += [alt]
                grid['az'] += [az]
                grid['done'] += [False]

        # to dataframe
        grid = pd.DataFrame(grid).set_index(['alt', 'az'])

        # get acquisition unit
        acquisition: IAcquisition = self.proxy(self._acquisition, IAcquisition)

        # loop until finished
        while not self._abort.is_set():
            # get all entries without offset measurements
            todo = list(grid[~grid['done']].index)
            if len(todo) / len(grid) < self._finish:
                log.info('Finished.')
                break
            log.info('Grid points left to do: %d', len(todo))

            # get moon
            moon = self.observer.moon_altaz(Time.now())

            # try to find a good point
            while True:
                # pick a random index and remove from list
                alt, az = random.sample(todo, 1)[0]
                todo.remove((alt, az))
                altaz = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame='altaz', obstime=Time.now(),
                                 location=self.observer.location)

                # moon far enough away?
                if altaz.separation(moon).degree > 30:
                    # yep, stop here
                    break

                # to do list empty?
                if len(todo) == 0:
                    # could not find a grid point
                    log.info('Could not find a suitable grid point, resetting todo list for next entry...')
                    todo = list(grid.index)
                    continue

            # aborted?
            if self._abort.is_set():
                return

            # get RA/Dec
            radec = altaz.icrs

            # log finding
            log.info('Picked grid point at Alt=%.2f, Az=%.2f (%s).', alt, az, radec.to_string('hmsdms'))

            # acquire target
            try:
                acquisition.acquire_target(self._exp_time, float(radec.ra.degree), float(radec.dec.degree)).wait()
            except ValueError:
                log.info('Could not acquire target.')
                continue

            # finished
            grid.loc[alt, az] = True

        # finished
        if self._abort.is_set():
            log.info('Pointing series aborted.')
        else:
            log.info('Pointing series finished.')

    def abort(self, *args, **kwargs):
        """Abort current actions."""
        self._abort.set()


__all__ = ['PointingSeries']
