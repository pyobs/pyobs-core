import logging
import random

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs import PyObsModule
from pyobs.interfaces import IAcquisition, IMastermind
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingSeries(PyObsModule, IMastermind):
    """Module for running pointing series."""

    def __init__(self, min_alt: int = 30, max_alt: int = 85, num_alt: int = 8, num_az: int = 24, finish: int = 90,
                 exp_time: int = 1000, acquisition: str = 'acquisition', *args, **kwargs):
        """Initialize a new auto focus system.

        Args:
            min_alt: Mininum altitude to use.
            max_alt: Maximum altidude to use.
            num_alt: Number of altitude points to create on grid.
            num_az: Number of azimuth points to create on grid.
            finish: When this number in percent of points have been finished, terminate mastermind.
            exp_time: Exposure time in ms.
            acquisition: IAcquisition unit to use.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store
        self._min_alt = min_alt
        self._max_alt = max_alt
        self._num_alt = num_alt
        self._num_az = num_az
        self._finish = 1. - finish / 100.
        self._exp_time = exp_time
        self._acquisition = acquisition

        # add thread func
        self._add_thread_func(self._run_thread, False)

    def _run_thread(self):
        """Run a pointing series."""

        # create grid
        grid = {'alt': [], 'az': [], 'done': []}
        for az in np.linspace(0, 360 - 360 / self._num_az, self._num_az):
            for alt in np.linspace(self._min_alt, self._max_alt, self._num_alt):
                grid['alt'] += [alt]
                grid['az'] += [az]
                grid['done'] += [False]

        # to dataframe
        grid = pd.DataFrame(grid).set_index(['alt', 'az'])

        # get acquisition unit
        acquisition: IAcquisition = self.proxy(self._acquisition, IAcquisition)

        # loop until finished
        while not self.closing.is_set():
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
                # aborted?
                if self.closing.is_set():
                    return

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

            # get RA/Dec
            radec = altaz.icrs

            # log finding
            log.info('Picked grid point at Alt=%.2f, Az=%.2f (%s).', alt, az, radec.to_string('hmsdms'))

            # acquire target and process result
            try:
                acq = acquisition.acquire_target(self._exp_time, float(radec.ra.degree), float(radec.dec.degree)).wait()
                if acq is not None:
                    self._process_acquisition(**acq)
            except ValueError:
                log.info('Could not acquire target.')
                continue

            # finished
            grid.loc[alt, az] = True

        # finished
        if self.closing.is_set():
            log.info('Pointing series aborted.')
        else:
            log.info('Pointing series finished.')

    def _process_acquisition(self, datetime: str, ra: float, dec: float, alt: float, az: float,
                             off_ra: float = None, off_dec: float = None, off_alt: float = None, off_az: float = None):
        """Process the result of the acquisition. Either ra_off/dec_off or alt_off/az_off must be given.

        Args:
            datetime: Date and time of observation.
            ra: Right ascension without offsets at destination.
            dec: Declination without offsets at destination.
            alt: Altitude without offsets at destination.
            az: Azimuth without offsets at destination.
            off_ra: Found RA offset.
            off_dec: Found Dec offset.
            off_alt: Found Alt offset.
            off_az: Found Az offset.
        """
        pass


__all__ = ['PointingSeries']
