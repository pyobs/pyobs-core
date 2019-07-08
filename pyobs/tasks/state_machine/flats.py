import threading

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import fits
import numpy as np
import logging
from enum import Enum
from typing import Tuple
from py_expression_eval import Parser

from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow
from pyobs.utils.threads import Future
from pyobs.utils.time import Time
from .task import StateMachineTask


log = logging.getLogger(__name__)


class FlatsTask(StateMachineTask):
    """Take flat fields in a given filter."""

    class State(Enum):
        INIT = 'init'
        WAITING = 'waiting'
        TESTING = 'testing'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, filter: str = None, binning: Tuple = (1, 1), bias: float = None, function: str = None,
                 target_count: float = 30000, min_exptime: float = 0.5, max_exptime: float = 5,
                 test_frame: Tuple = (45, 45, 10, 10), counts_frame: Tuple = (0, 0, 100, 100),
                 telescope: str = None, camera: str = None, filters: str = None, *args, **kwargs):
        """Initializes a new Flats Task.

        Args:
            filter: Name of filter.
            binning: Binning to use.
            bias: Bias level for given binning.
            function: Function f(h) to describe ideal exposure time as a function of solar elevation h,
                i.e. something like exp(-0.9*(h+3.9))
            target_count: Count rate to aim for.
            min_exptime: Minimum exposure time.
            max_exptime: Maximum exposure time.
            test_frame: Tupel (left, top, width, height) in percent that describe the frame for on-sky testing.
            counts_frame: Tupel (left, top, width, height) in percent that describe the frame for calculating mean
                count rate.
            telescope: Name of ITelescope module to use.
            camera: Name of ICamera module to use.
            filters: Name of IFilters module to use.
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._filter = filter
        self._binning = binning
        self._bias = bias
        self._target_count = target_count
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime
        self._test_frame = test_frame
        self._counts_frame = counts_frame

        # parse function
        parser = Parser()
        self._function = parser.parse(function)

        # state machine
        self._state = FlatsTask.State.INIT

        # current exposure time
        self._exptime = None

        # telescope and camera
        self._telescope_name = telescope
        self._telescope = None
        self._camera_name = camera
        self._camera = None
        self._filters_name = filters
        self._filters = None

    def __call__(self, closing_event: threading.Event, *args, **kwargs):
        """Run the task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # which state?
        if self._state == FlatsTask.State.INIT:
            # init task
            self._init()
        elif self._state == FlatsTask.State.WAITING:
            # wait until exposure time reaches good time
            self._wait(closing_event)
        elif self._state == FlatsTask.State.TESTING:
            # do actual tests on sky for exposure time
            self._flat_field(testing=True)
        elif self._state == FlatsTask.State.RUNNING:
            # take flat fields
            self._flat_field(testing=False)
        else:
            # wait
            closing_event.wait(10)

    def _init(self):
        """Init task."""

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
        altaz = SkyCoord(alt=80 * u.deg, az=sun.az + 180 * u.degree, obstime=Time.now(),
                         location=self.observer.location, frame='altaz')
        logging.info('Sweet spot for flat fielding is at alt=80°, az=%.2f°', altaz.az.degree)
        radec = altaz.icrs

        # move telescope
        log.info('Moving telescope to %s...', radec.to_string('hmsdms'))
        future_track = self._telescope.track_radec(radec.ra.degree, radec.dec.degree)

        # get filter from first step and set it
        log.info('Setting filter to %s...', self._filter)
        future_filter = self._filters.set_filter(self._filter)

        # wait for both
        Future.wait_all([future_track, future_filter])
        log.info('Finished initializing task.')

        # change stats
        log.info('Waiting for flat-field time...')
        self._state = FlatsTask.State.WAITING

    def _wait(self, closing_event: threading.Event):
        # get solar elevation and evaluate function
        sun = self.observer.sun_altaz(Time.now())
        exptime = self._function.evaluate({'h': sun.alt.degree})
        log.info('Calculated optimal exposure time of %.2fs at solar elevation of %.2f°.', exptime, sun.alt.degree)

        # in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # yes, change state
            log.info('Starting to take test flat-fields...')
            self._state = FlatsTask.State.TESTING
            self._exptime = exptime
        else:
            # sleep a little
            closing_event.wait(10)

    def _flat_field(self, testing: bool = False):
        # set binning
        if isinstance(self._camera, ICameraBinning):
            log.info('Setting camera binning to %dx%d...', **self._binning)
            self._camera.set_binning(*self._binning)

        # set window
        if isinstance(self._camera, ICameraWindow):
            # get full frame
            left, top, width, height = self._camera.get_full_frame().wait()

            # if testing, take test frame, otherwise use full frame
            if testing:
                left, top, width, height = int(left + self._test_frame[0] / 100 * width),\
                                           int(top + self._test_frame[1] / 100 * width),\
                                           int(self._test_frame[2] / 100 * width),\
                                           int(self._test_frame[3] / 100 * height)
            log.info('Setting camera window to %dx%d at %d,%d...', width, height, left, top)
            self._camera.set_window(left, top, width, height).wait()

        # do exposures
        log.info('Exposing flat field for %.2fs...', self._exptime)
        filename = self._camera.expose(exposure_time=self._exptime * 1000., image_type=ICamera.ImageType.FLAT).wait()
        self._exposure += 1

        # download image
        try:
            log.info('Downloading image...')
            with self.vfs.open_file(filename[0], 'rb') as f:
                tmp = fits.open(f, memmap=False)
                flat_field = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                tmp.close()
        except FileNotFoundError:
            log.error('Could not download image.')
            return

        # get data in counts frame
        width, height = flat_field.data.shape
        f = self._counts_frame
        in_data = flat_field.data[int(f[0] / 100 * width):int((f[0] + f[2]) / 100 * width),
                                  int(f[1] / 100 * height):int((f[1] + f[3]) / 100 * height)]

        # get mean
        mean = np.mean(in_data)
        log.info('Got a flat field with mean counts of %.2f.', mean)

        # calculate next exposure time
        exptime = self._exptime / (mean - self._bias) * (self._target_count - self._bias)
        log.info('Calculated new exposure time to be %.2fs.', exptime)

        # in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # testing or flat-fielding?
            if testing:
                # go to actual flat fielding
                log.info('Starting to store flat-fields...')
                self._state = FlatsTask.State.RUNNING
            else:
                # keep going
                self._exptime = exptime

        else:
            # we're finished
            log.info('Left exposure time range for taking flats.')

            # finish
            self.finish()

    def finish(self):
        """Final steps for a task."""

        # already finished?
        if self._state == FlatsTask.State.FINISHED:
            return

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
        self._state = FlatsTask.State.FINISHED


__all__ = ['FlatsTask']
