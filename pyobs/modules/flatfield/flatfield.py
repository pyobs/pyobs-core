import logging
import threading
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import fits
from astropy.time import TimeDelta
import typing
from py_expression_eval import Parser
from enum import Enum

from pyobs.interfaces import ICamera, IFlatField, IFilters, ITelescope, ICameraWindow, ICameraBinning
from pyobs import PyObsModule
from pyobs.modules import timeout
from pyobs.utils.time import Time
from pyobs.utils.threads import Future

log = logging.getLogger(__name__)


class FlatField(PyObsModule, IFlatField):
    """Module for auto-focusing a telescope."""

    class Twilight(Enum):
        DUSK = 'dusk'
        DAWN = 'dawn'

    class State(Enum):
        INIT = 'init'
        WAITING = 'waiting'
        TESTING = 'testing'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, telescope: typing.Union[str, ITelescope], camera: typing.Union[str, ICamera],
                 filters: typing.Union[str, IFilters], functions: typing.Dict[str, str] = None,
                 target_count: float = 30000, min_exptime: float = 0.5, max_exptime: float = 5,
                 test_frame: tuple = (45, 45, 10, 10), counts_frame: tuple = (0, 0, 100, 100),
                 *args, **kwargs):
        """Initialize a new flat fielder.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            filters: Name of IFilters, if any.
            functions: Function f(h) for each filter to describe ideal exposure time as a function of solar
                elevation h, i.e. something like exp(-0.9*(h+3.9))
            target_count: Count rate to aim for.
            min_exptime: Minimum exposure time.
            max_exptime: Maximum exposure time.
            test_frame: Tupel (left, top, width, height) in percent that describe the frame for on-sky testing.
            counts_frame: Tupel (left, top, width, height) in percent that describe the frame for calculating mean
                count rate.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope, camera, and filters
        self._telescope = telescope
        self._camera = camera
        self._filters = filters
        self._target_count = target_count
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime
        self._test_frame = test_frame
        self._counts_frame = counts_frame

        # abort event
        self._abort = threading.Event()

        # state machine
        self._state = FlatField.State.INIT

        # current exposure time
        self._exptime = None

        # exposures to do
        self._exposures_left = 0

        # bias level
        self._bias_level = None

        # which twilight are we in?
        self._twilight = None

        # telescope and camera
        self._telescope_name = telescope
        self._telescope = None
        self._camera_name = camera
        self._camera = None
        self._filters_name = filters
        self._filters = None

        # parse function
        if functions is None:
            functions = {}
        self._functions = {filter_name: Parser().parse(func) for filter_name, func in functions.items()}

    def open(self):
        """Open module"""
        PyObsModule.open(self)

        # check telescope, camera, and filters
        try:
            self.proxy(self._telescope, ITelescope)
            self.proxy(self._camera, ICamera)
            self.proxy(self._filters, IFilters)
        except ValueError:
            log.warning('Either telescope, camera or filters do not exist or are not of correct type at the moment.')

    def close(self):
        """Close module."""

    @timeout(3600000)
    def flat_field(self, filter_name: str, count: int = 20, binning: int = 1, *args, **kwargs):
        """Do a series of flat fields in the given filter.

        Args:
            filter_name: Name of filter.
            count: Number of images to take.
            binning: Binning to use.
        """
        log.info('Performing flat fielding...')

        # reset
        self._abort = threading.Event()
        self._state = FlatField.State.INIT
        self._exposures_left = count

        # get telescope
        log.info('Getting proxy for telescope...')
        self._telescope: ITelescope = self.proxy(self._telescope_name, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        self._camera: ICamera = self.proxy(self._camera_name, ICamera)

        # get filter wheel
        log.info('Getting proxy for filter wheel...')
        self._filters: IFilters = self.proxy(self._filters_name, IFilters)

        # run until state is finished or we aborted
        while not self._abort.is_set() and self._state != FlatField.State.FINISHED:
            # which state?
            if self._state == FlatField.State.INIT:
                # init task
                self._init_system(filter_name, binning)
            elif self._state == FlatField.State.WAITING:
                # wait until exposure time reaches good time
                self._wait(filter_name, binning)
            elif self._state == FlatField.State.TESTING:
                # do actual tests on sky for exposure time
                self._flat_field(testing=True)
            elif self._state == FlatField.State.RUNNING:
                # take flat fields
                self._flat_field(testing=False)

        # stop telescope
        log.info('Stopping telescope...')
        self._telescope.stop_motion().wait()

        # release proxies
        self._telescope = None
        self._camera = None
        self._filters = None

        # finished
        log.info('Finished task.')
        self._state = FlatField.State.FINISHED

    def _get_bias(self) -> float:
        """Take bias image to determine bias level.

        Returns:
            Average bias level.
        """
        log.info('Taking BIAS image to determine average level...')

        # set full frame
        if isinstance(self._camera, ICameraWindow):
            full_frame = self._camera.get_full_frame().wait()
            self._camera.set_window(*full_frame).wait()

        # take image
        filename = self._camera.expose(0, ICamera.ImageType.BIAS, broadcast=False).wait()

        # download image
        with self.vfs.open_file(filename[0], 'rb') as f:
            # get average value
            tmp = fits.open(f, memmap=False)
            avg = float(np.mean(tmp['SCI'].data))
            tmp.close()

        # return it
        log.info('Found average BIAS level of %.2f...', avg)
        return avg

    def _init_system(self, filter_name: str, binning: int = 1):
        """Initialize whole system.

        Args:
            filter_name: Name of filter.
            binning: Binning to use.
        """

        # set binning
        if isinstance(self._camera, ICameraBinning):
            log.info('Setting binning to %dx%d...', binning, binning)
            self._camera.set_binning(binning, binning)

        # get bias level
        self._bias_level = self._get_bias()

        # calculate Alt/Az position of sun
        sun = self.observer.sun_altaz(Time.now())
        log.info('Sun is currently located at alt=%.2f°, az=%.2f°', sun.alt.degree, sun.az.degree)

        # which twilight are we in?
        sun_10min = self.observer.sun_altaz(Time.now() + TimeDelta(10 * u.minute))
        self._twilight = FlatField.Twilight.DUSK if sun_10min.alt.degree < sun.alt.degree else FlatField.Twilight.DAWN
        log.info('We are currently in %s twilight.', self._twilight.value)

        # get sweet spot for flat-fielding
        altaz = SkyCoord(alt=80 * u.deg, az=sun.az + 180 * u.degree, obstime=Time.now(),
                         location=self.observer.location, frame='altaz')
        log.info('Sweet spot for flat fielding is at alt=80°, az=%.2f°', altaz.az.degree)

        # move telescope
        log.info('Moving telescope to Alt=80, Az=%.2f...', altaz.az.degree)
        future_track = self._telescope.move_altaz(80, altaz.az.degree)

        # get filter from first step and set it
        log.info('Setting filter to %s...', filter_name)
        future_filter = self._filters.set_filter(filter_name)

        # wait for both
        Future.wait_all([future_track, future_filter])
        log.info('Finished initializing system.')

        # change stats
        log.info('Waiting for flat-field time...')
        self._state = FlatField.State.WAITING

    def _wait(self, filter_name: str, binning: int = 1):
        """Wait for flat-field time.

        Args:
            filter_name: Name of filter to wait for.
            binning: Binning to use.
        """

        # get solar elevation and evaluate function
        sun = self.observer.sun_altaz(Time.now())
        exptime = self._functions[filter_name].evaluate({'h': sun.alt.degree})

        # scale with binning
        exptime /= binning * binning
        log.info('Calculated optimal exposure time of %.2fs in %dx%d at solar elevation of %.2f°.',
                 exptime, binning, binning, sun.alt.degree)

        # in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # yes, change state
            log.info('Starting to take test flat-fields...')
            self._state = FlatField.State.TESTING
            self._exptime = exptime
        else:
            # sleep a little
            self._abort.wait(10)

    def _flat_field(self, testing: bool = False):
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

            # set it
            log.info('Setting camera window to %dx%d at %d,%d...', width, height, left, top)
            self._camera.set_window(left, top, width, height).wait()

        # do exposures, do not broadcast while testing
        log.info('Exposing flat field for %.2fs...', self._exptime)
        filename = self._camera.expose(exposure_time=int(self._exptime * 1000.), image_type=ICamera.ImageType.SKYFLAT,
                                       broadcast=not testing).wait()

        # decrease count
        if not testing:
            self._exposures_left -= 1

        # download image
        try:
            log.info('Downloading image...')
            with self.vfs.open_file(filename[0], 'rb') as f:
                tmp = fits.open(f, memmap=False)
                flat_field = np.copy(tmp[0].data)
                tmp.close()
        except FileNotFoundError:
            log.error('Could not download image.')
            return

        # get data in counts frame
        width, height = flat_field.shape
        f = self._counts_frame
        in_data = flat_field[int(f[0] / 100 * width):int((f[0] + f[2]) / 100 * width),
                             int(f[1] / 100 * height):int((f[1] + f[3]) / 100 * height)]

        # get mean
        mean = np.mean(in_data)
        log.info('Got a flat field with mean counts of %.2f.', mean)

        # calculate factor for new exposure time
        factor = (self._target_count - self._bias_level) / (mean - self._bias_level)

        # limit factor to 0.5-1.5
        factor = min(1.5, max(0.5, factor))

        # calculate next exposure time
        exptime = self._exptime * factor
        log.info('Calculated new exposure time to be %.2fs.', exptime)

        # in boundaries?
        if self._min_exptime <= exptime <= self._max_exptime:
            # testing or flat-fielding?
            if testing:
                # go to actual flat fielding
                log.info('Starting to store flat-fields...')
                self._state = FlatField.State.RUNNING

            else:
                # finished?
                if self._exposures_left <= 0:
                    log.info('Finished all requested flat-fields..')
                    self._state = FlatField.State.FINISHED
                # keep going
                self._exptime = exptime

        else:
            # testing or flat-fielding?
            if testing:
                # TODO: decide on sunset/sunrise, whether to wait or not
                pass

            else:
                # we're finished
                log.info('Left exposure time range for taking flats.')
                self._state = FlatField.State.FINISHED

    def flat_field_status(self, *args, **kwargs) -> dict:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        raise NotImplementedError

    @timeout(20000)
    def abort(self, *args, **kwargs):
        """Abort current actions."""
        self._abort.set()


__all__ = ['FlatField']
