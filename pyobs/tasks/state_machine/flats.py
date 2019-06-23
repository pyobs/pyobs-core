import threading

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import fits
import numpy as np
import logging
import time
from enum import Enum
from typing import Tuple
from py_expression_eval import Parser

from pyobs.interfaces import ITelescope, IFocuser, ICamera, IFilters
from pyobs.utils.threads import Future
from pyobs.utils.time import Time
from .task import StateMachineTask


log = logging.getLogger(__name__)


class FlatsTask(StateMachineTask):
    """Take flat fields in a given filter."""

    def __init__(self, filter: str = None, binning: Tuple = (1, 1), bias: float = None, function: str = None,
                 target_adu: float = 30000, min_exptime: float = 0.5, max_exptime: float = 5,
                 telescope: str = None, camera: str = None, filters: str = None, *args, **kwargs):
        """Initializes a new Flats Task.

        Args:
            filter: Name of filter.
            binning: Binning to use.
            bias: Bias level for given binning.
            function: Function f(h) to describe ideal exposure time as a function of solar elevation h,
                i.e. something like exp(-0.9*(h+3.9))
            target_adu: Count rate to aim for.
            min_exptime: Minimum exposure time.
            max_exptime: Maximum exposure time.
            telescope: Name of ITelescope module to use.
            camera: Name of ICamera module to use.
            filters: Name of IFilters module to use.
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._filter = filter
        self._binning = binning
        self._bias = bias
        self._target_adu = target_adu
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime

        # parse function
        parser = Parser()
        self._function = parser.parse(function)

        # state machine
        self._waiting = True
        self._exptime = None

        # telescope and camera
        self._telescope_name = telescope
        self._telescope = None
        self._camera_name = camera
        self._camera = None
        self._filters_name = filters
        self._filters = None

    def _init(self, closing_event: threading.Event):
        """Init task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # get telescope and camera
        self._telescope: ITelescope = self.comm[self._telescope_name]
        self._camera: ICamera = self.comm[self._camera_name]
        self._filters: IFilters = self.comm[self._filters_name]

        # reset exposures
        self._exposure = 0

        # calculate Alt/Az position of sun
        sun = self.observer.sun_altaz(Time.now())
        logging.info('Sun is currently located at alt=%.2f°, az=%.2f°', sun.alt.degree, sun.az.degree)

        # get sweet spot for flat-fielding
        az = sun.az.degree + 180
        altaz = SkyCoord(alt=80 * u.deg, az=sun.az + 180 * u.degree, obstime=Time.now(),
                         location=self.observer.location, frame='altaz')
        logging.info('Sweet spot for flat fielding is at alt=80°, az=%.2f°', altaz.az.degree)
        radec = altaz.icrs

        # move telescope
        log.info('Moving telescope to %s...', radec.to_string('hmsdms'))
        future_track = self._telescope.track(radec.ra.degree, radec.dec.degree)

        # get filter from first step and set it
        log.info('Setting filter to %s...', self._filter)
        future_filter = self._filters.set_filter(self._filter)

        # wait for both
        Future.wait_all([future_track, future_filter])

    def _step(self, closing_event: threading.Event):
        """Single step for a task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # which state are we in?
        if self._waiting:
            # wait until time for flat fields has come
            self._wait()
        else:
            # actually take flats
            self._progress()

    def _wait(self):
        # get solar elevation and evaluate function
        sun = self.observer.sun_altaz(Time.now())
        exptime = self._function.evaluate({'h': sun.alt.degree})

        # in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # yes, change state
            log.info('Starting to take flat-fields...')
            self._waiting = False
            self._exptime = exptime
        else:
            # sleep a little
            time.sleep(10)

    def _progress(self):
        # do exposures
        log.info('Exposing flat field for %.2fs each...', self._exptime)
        filename = self._camera.expose(exposure_time=self._exptime * 1000., image_type=ICamera.ImageType.FLAT).wait()
        self._exposure += 1

        # download image
        try:
            with self.vfs.open_file(filename[0], 'rb') as f:
                tmp = fits.open(f, memmap=False)
                flat_field = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                tmp.close()
        except FileNotFoundError:
            log.error('Could not download image.')
            return

        # get mean
        mean = np.mean(flat_field.data)
        log.info('Got a flat field with %.2f counts.', mean)

        # calculate next exposure time
        exptime = self._exptime / (mean - self._bias) * (self._target_adu - self._bias)
        log.info('Calculated new exposure time to be %.2fs.', exptime)

        # still in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # yes, keep going
            self._exptime = exptime
        else:
            # we're finished
            log.info('Left exposure time range for taking flats.')

            # finish
            self._finish()

    def _finish(self):
        """Final steps for a task."""

        # stop telescope
        log.info('Stopping telescope...')
        self._telescope.stop_motion().wait()

        # release proxies
        self._telescope = None
        self._camera = None
        self._filters = None

        # finished
        log.info('Finished task.')

        # change state
        self._state = StateMachineTask.State.FINISHED


__all__ = ['FlatsTask']
