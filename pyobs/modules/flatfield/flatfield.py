import io
import logging
import threading
import numpy as np
import pandas as pd
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
from pyobs.utils.fits import fitssec

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
                 test_frame: tuple = (45, 45, 10, 10), counts_frame: tuple = (25, 25, 75, 75),
                 log: str = '/pyobs/flatfield.csv', *args, **kwargs):
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
            log: Log file to write.
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
        self._log_file = log

        # abort event
        self._abort = threading.Event()

        # state machine
        self._state = FlatField.State.INIT

        # current exposure time
        self._exptime = None

        # exposures to do
        self._exposures_total = 0
        self._exposures_done = 0

        # bias level
        self._bias_level = None

        # which twilight are we in?
        self._twilight = None

        # current request
        self._cur_filter = None
        self._cur_binning = None

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
        PyObsModule.close(self)
        self._abort.set()

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
        self._exposures_total = count
        self._exposures_done = 0
        self._cur_filter = filter_name
        self._cur_binning = binning

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
                self._init_system()
            elif self._state == FlatField.State.WAITING:
                # wait until exposure time reaches good time
                self._wait()
            elif self._state == FlatField.State.TESTING:
                # do actual tests on sky for exposure time
                self._testing()
            elif self._state == FlatField.State.RUNNING:
                # take flat fields
                self._flat_field()

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

    def _init_system(self):
        """Initialize whole system."""

        # set binning
        if isinstance(self._camera, ICameraBinning):
            log.info('Setting binning to %dx%d...', self._cur_binning, self._cur_binning)
            self._camera.set_binning(self._cur_binning, self._cur_binning)

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
        log.info('Setting filter to %s...', self._cur_filter)
        future_filter = self._filters.set_filter(self._cur_filter)

        # wait for both
        Future.wait_all([future_track, future_filter])
        log.info('Finished initializing system.')

        # change stats
        log.info('Waiting for flat-field time...')
        self._state = FlatField.State.WAITING

    def _wait(self):
        """Wait for flat-field time."""

        # get solar elevation and evaluate function
        sun_alt, self._exptime = self._eval_function(Time.now())
        log.info('Calculated optimal exposure time of %.2fs in %dx%d at solar elevation of %.2f°.',
                 self._exptime, self._cur_binning, self._cur_binning, sun_alt)

        # then evaluate exposure time within a larger range
        state = self._eval_exptime(self._min_exptime * 0.5, self._max_exptime * 2.0)
        if state < 0:
            log.info('Sleeping a little...')
            self._abort.wait(10)
        elif state == 0:
            log.info('Starting to take test flat-fields...')
            self._state = FlatField.State.TESTING
        else:
            log.info('Missed flat-fielding time, finish task...')
            self._state = FlatField.State.FINISHED

    def _eval_function(self, time: Time) -> (float, float):
        """Evaluate function for given filter at given time.

        Args:
            time: Time to evaluate function at.

        Returns:
            Estimated exposure time.
        """

        # get solar elevation and evaluate function
        sun = self.observer.sun_altaz(time)
        exptime = self._functions[self._cur_filter].evaluate({'h': sun.alt.degree})

        # scale with binning
        exptime /= self._cur_binning * self._cur_binning
        return sun.alt.degree, exptime

    def _eval_exptime(self, min_exptime: float = None, max_exptime: float = None) -> int:
        """Evaluates current exposure time. Sets new state or waits of necessary.

        Returns:
            -1, if we have to wait, 0 during flat-field time and 1 if it has passed.
        """

        # no min/max given?
        if min_exptime is None:
            min_exptime = self._min_exptime
        if max_exptime is None:
            max_exptime = self._max_exptime

        # need to wait, change status or are we finished?
        if (self._twilight == FlatField.Twilight.DUSK and self._exptime > max_exptime) or \
           (self._twilight == FlatField.Twilight.DAWN and self._exptime < min_exptime):
            # in DUSK, if exptime is greater than max exptime, we're past flatfielding time
            # in DAWN, if exptime is less than min exptime, we're past flatfielding time
            return 1
        elif (self._twilight == FlatField.Twilight.DUSK and self._exptime < min_exptime) or \
             (self._twilight == FlatField.Twilight.DAWN and self._exptime > max_exptime):
            # in DUSK, if exptime is less than max exptime, we still need to wait
            # in DAWN, if exptime is greater than min exptime, we still need to wait
            return -1
        else:
            # otherwise it seems that we're in the middle of flat-fielding time
            return 0

    def _set_window(self, testing: bool):
        """Set camera window.

        Args:
            testing: Whether we're in testing mode or not.
        """
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

    def _download_image(self, filename: str) -> typing.Union[np.ndarray, None]:
        try:
            log.info('Downloading image...')
            with self.vfs.open_file(filename, 'rb') as f:
                tmp = fits.open(f, memmap=False)
                image = fits.PrimaryHDU(tmp['SCI'].data, header=tmp['SCI'].header)
                tmp.close()
                return image
        except FileNotFoundError:
            log.error('Could not download image.')
            return None

    def _get_image_median(self, image, frame=None) -> float:
        """Returns median of image after trimming it to TRIMSEC and to given frame.

        Args:
            image: Image to calculate median for.
            frame: Frame coordinates as (width, top, width, height) in percent of full frame.

        Returns:
            Median of image.
        """

        # trim image to TRIMSEC
        data = fitssec(image, 'TRIMSEC')

        # cut to frame
        if frame is not None:
            width, height = data.shape
            data = data[int(frame[0] / 100 * width):int((frame[0] + frame[2]) / 100 * width),
                        int(frame[1] / 100 * height):int((frame[1] + frame[3]) / 100 * height)]

        # return median
        return np.median(data)

    def _calc_new_exptime(self, median: float) -> float:
        """Calculate new exposure time.

        Args:
            median: Median of last exposure.

        Returns:
            New exposure time.
        """
        # calculate factor for new exposure time
        factor = (self._target_count - self._bias_level) / (median - self._bias_level)

        # limit factor to 0.1-10
        factor = min(10., max(0.1, factor))

        # calculate next exposure time
        return self._exptime * factor

    def _analyse_image(self, filename: str):
        # download image
        flat_field = self._download_image(filename[0])
        if flat_field is None:
            return

        # get median from image
        median = self._get_image_median(flat_field, self._counts_frame)
        log.info('Got a flat field with median counts of %.2f.', median)

        # calculate new exposure time
        self._exptime = self._calc_new_exptime(median)
        log.info('Calculated new exposure time to be %.2fs.', self._exptime)

    def _testing(self):
        """Take flat-fields but don't store them."""

        # set window
        self._set_window(testing=True)

        # do exposures, do not broadcast while testing
        log.info('Exposing test flat field for %.2fs...', self._exptime)
        filename = self._camera.expose(exposure_time=int(self._exptime * 1000.),
                                       image_type=ICamera.ImageType.SKYFLAT,
                                       broadcast=False).wait()

        # analyse image
        self._analyse_image(filename[0])

        # then evaluate exposure time
        state = self._eval_exptime()
        if state < 0:
            log.info('Sleeping a little...')
            self._abort.wait(10)
        elif state == 0:
            log.info('Starting to store flat-fields...')
            self._state = FlatField.State.RUNNING
        else:
            log.info('Missed flat-fielding time, finish task...')
            self._state = FlatField.State.FINISHED

    def _flat_field(self):
        """Take flat-fields."""

        # set window
        self._set_window(testing=True)

        # do exposures, do not broadcast while testing
        now = Time.now()
        log.info('Exposing flat field %d/%d for %.2fs...', self._exposures_done, self._exposures_total, self._exptime)
        filename = self._camera.expose(exposure_time=int(self._exptime * 1000.),
                                       image_type=ICamera.ImageType.SKYFLAT).wait()

        # increase count and quite here, if finished
        self._exposures_done += 1
        if self._exposures_done >= self._exposures_total:
            log.info('Finished all requested flat-fields..')
            self._state = FlatField.State.FINISHED
            return

        # analyse image
        self._analyse_image(filename[0])

        # write it to log
        sun = self.observer.sun_altaz(now)
        self._write_log(now.datetime, sun.alt.degree)

        # then evaluate exposure time
        state = self._eval_exptime()
        if state < 0:
            log.info('Going back to testing...')
            self._state = FlatField.State.TESTING
        elif state == 0:
            pass
        else:
            log.info('Missed flat-fielding time, finish task...')
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

    def _write_log(self, dt, sol_alt):
        """Write log file entry."""

        # do we have a log file?
        if self._log_file is not None:
            # try to load it
            try:
                with self.open_file(self._log_file, 'r') as f:
                    # read file
                    data = pd.read_csv(f, index_col=False)

            except (FileNotFoundError, ValueError):
                # init empty file
                data = pd.DataFrame(dict(datetime=[], solalt=[], exptime=[], counts=[], filter=[], binning=[]))

            # add data
            data = data.append(dict(datetime=dt, solalt=sol_alt, exptime=self._exptime, counts=self._target_count,
                                    filter=self._cur_filter, binning=self._cur_binning),
                               ignore_index=True)

            # write file
            with self.open_file(self._log_file, 'w') as f:
                with io.StringIO() as sio:
                    data.to_csv(sio, index=False)
                    f.write(sio.getvalue().encode('utf8'))


__all__ = ['FlatField']
