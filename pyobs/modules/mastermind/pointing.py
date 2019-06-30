import logging
import random
import numpy as np
import pandas as pd

from pyobs import PyObsModule

log = logging.getLogger(__name__)


class PointingMastermind(PyObsModule):
    """Mastermind that acts as a state machine."""

    def __init__(self, min_alt: int = 15, max_alt: int = 85, num_alt: int = 8, num_az: int = 24, finish: int = 90,
                 *args, **kwargs):
        """Initialize a new auto focus system.

        Args:
            min_alt: Mininum altitude to use.
            max_alt: Maximum altidude to use.
            num_alt: Number of altitude points to create on grid.
            num_az: Number of azimuth points to create on grid.
            finish: When this number in percent of points have been finished, terminate mastermind.
        """
        PyObsModule.__init__(self, thread_funcs=self._run_thread, restart_threads=False, *args, **kwargs)

        # store
        self._finish = 1. - finish / 100.

        # create grid
        grid = {'alt': [], 'az': [], 'done': []}
        for az in np.linspace(0, 360 - 360 / num_az, num_az):
            for alt in np.linspace(min_alt, max_alt, num_alt):
                grid['alt'] += [alt]
                grid['az'] += [az]
                grid['done'] += [False]

        # to dataframe
        self._grid = pd.DataFrame(grid).set_index(['alt', 'az'])

    def _run_thread(self):
        while not self.closing.is_set():
            # get all entries without offset measurements
            todo = self._grid[~self._grid['done']]
            if len(todo) / len(self._grid) < self._finish:
                log.info('Finished.')
                break
            log.info('Grid points left to do: %d', len(todo))

            # pick a random index
            alt, az = random.sample(list(todo.index), 1)[0]
            log.info('Picked grid point at alt=%.2f, az=%.2f.', alt, az)

            # observe

            # finished
            self._grid.loc[alt, az] = True


            self.closing.wait(1)


__all__ = ['PointingMastermind']
