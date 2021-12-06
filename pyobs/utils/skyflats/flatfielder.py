from __future__ import annotations
import threading
from enum import Enum
import logging
from typing import Dict, Union, Callable, Optional, Tuple, Any, cast
import astropy.units as u
from astroplan import Observer
from astropy.time import TimeDelta
import numpy as np

from pyobs.object import get_safe_object, Object
from pyobs.utils.enums import ImageType
from pyobs.utils.fits import fitssec
from pyobs.utils.threads import Future
from pyobs.utils.time import Time
from pyobs.vfs import VirtualFileSystem
from .exptimeeval import ExpTimeEval
from .pointing import SkyFlatsBasePointing
from pyobs.interfaces import ITelescope, ICamera, IFilters, IExposureTime, IBinning, \
    IWindow, IImageType
from ...images import Image

log = logging.getLogger(__name__)


class FlatFielder(Object):
    """Automatized flat-fielding."""
    __module__ = 'pyobs.utils.skyflats'

    class Twilight(Enum):
        DUSK = 'dusk'
        DAWN = 'dawn'

    class State(Enum):
        INIT = 'init'
        WAITING = 'waiting'
        TESTING = 'testing'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, functions: Union[str, Dict[str, Union[str, Dict[str, str]]]],
                 target_count: float = 30000, min_exptime: float = 0.5, max_exptime: float = 5,
                 test_frame: Optional[Tuple[float, float, float, float]] = None,
                 counts_frame: Optional[Tuple[float, float, float, float]] = None, allowed_offset_frac: float = 0.2,
                 min_counts: int = 100, pointing: Optional[Union[Dict[str, Any], SkyFlatsBasePointing]] = None,
                 callback: Optional[Callable[..., Any]] = None, **kwargs: Any):
        """Initialize a new flat fielder.

        Args:
            functions: Function f(h) for each filter to describe ideal exposure time as a function of solar
                elevation h, i.e. something like exp(-0.9*(h+3.9)). See ExpTimeEval for details.
            target_count: Count rate to aim for.
            min_exptime: Minimum exposure time.
            max_exptime: Maximum exposure time.
            test_frame: Tupel (left, top, width, height) in percent that describe the frame for on-sky testing.
            counts_frame: Tupel (left, top, width, height) in percent that describe the frame for calculating mean
                count rate.
            allowed_offset_frac: Offset from target_count (given in fraction of it) that's still allowed for good
                flat-field
            min_counts: Minimum counts in frames.
            observer: Observer to use.
            vfs: VFS to use.
            callback: Callback function for statistics.
        """
        Object.__init__(self, **kwargs)

        # store stuff
        self._target_count = target_count
        self._min_exptime = min_exptime
        self._max_exptime = max_exptime
        self._test_frame = (45, 45, 10, 10) if test_frame is None else test_frame
        self._counts_frame = (25, 25, 75, 75) if counts_frame is None else counts_frame
        self._allowed_offset_frac = allowed_offset_frac
        self._min_counts = min_counts
        self._callback = callback

        # parse function
        self._eval = ExpTimeEval(self.observer, functions)

        # abort event
        self._abort = threading.Event()

        # pointing
        self._pointing: Optional[SkyFlatsBasePointing] = self.get_safe_object(pointing, SkyFlatsBasePointing)

        # state machine
        self._state = FlatFielder.State.INIT

        # current exposure time
        self._exptime = 0.

        # median of last image
        self._median = 0.

        # exposures to do
        self._exposures_total = 0
        self._exposures_done = 0
        self._exptime_done = 0.

        # bias level
        self._bias_level = 0.

        # which twilight are we in? just init something
        self._twilight = FlatFielder.Twilight.DAWN

        # current request
        self._cur_filter: Optional[str] = None
        self._cur_binning: Tuple[int, int] = (1, 1)

    def __call__(self, telescope: ITelescope, camera: ICamera, filters: Optional[IFilters] = None,
                 filter_name: Optional[str] = None, count: int = 20, binning: Tuple[int, int] = (1, 1)) -> State:
        """Calls next step in state machine.

        Args:
            telescope: Telescope to use.
            camera: Camera to use.
            filters: Filter wheel to use.
            filter_name: Name of filter to do flat fields in.
            count: Number of flat fields to take.
            binning: Binning for flat fields.

        Returns:
            Current state of flat fielder.
        """

        # camera must support exposure times
        if not isinstance(camera, IExposureTime):
            raise ValueError('Camera must support exposure times.')

        # store
        self._cur_filter = filter_name
        self._cur_binning = binning
        self._exposures_total = count

        # which state are we in?
        if self._state == FlatFielder.State.INIT:
            # init task
            self._init_system(telescope, camera, filters)
        elif self._state == FlatFielder.State.WAITING:
            # wait until exposure time reaches good time
            self._wait()
        elif self._state == FlatFielder.State.TESTING:
            # do actual tests on sky for exposure time
            self._testing(cast(ICameraProxy, camera))
        elif self._state == FlatFielder.State.RUNNING:
            # take flat fields
            self._flat_field(telescope, cast(ICameraProxy, camera))

        # return current state
        return self._state

    def reset(self) -> None:
        """Reset flat fielder"""
        self._state = FlatFielder.State.INIT
        self._exposures_done = 0
        self._exptime_done = 0
        if self._pointing is not None:
            self._pointing.reset()

    @property
    def has_filters(self) -> bool:
        """Returns True, if functions are based on filters."""
        return len(self._eval.filters) > 0

    @property
    def image_count(self) -> int:
        return self._exposures_done

    @property
    def total_exptime(self) -> float:
        return self._exptime_done

    def _initial_check(self) -> bool:
        """Do a quick initial check.

        Returns:
            False, if flat-field time for this filter is over, True otherwise.
        """

        # get solar elevation and evaluate function
        sun_alt, self._exptime = self._eval_function(Time.now())
        log.info('Calculated optimal exposure time of %.2fs in %dx%d at solar elevation of %.2f°.',
                 self._exptime, self._cur_binning[0], self._cur_binning[1], sun_alt)

        # then evaluate exposure time within a larger range
        state = self._eval_exptime(self._min_exptime * 0.5, self._max_exptime * 2.0)
        if state > 0:
            log.info('Missed flat-fielding time, finishing task...')
            self._state = FlatFielder.State.FINISHED
            return False
        else:
            log.info('Flat-field time is still coming, keep going...')
            return True

    def _init_system(self, telescope: ITelescopeProxy, camera: Union[ICameraProxy, IExposureTimeProxy],
                     filters: Optional[IFiltersProxy] = None) -> None:
        """Initialize whole system."""

        # which twilight are we in?
        if self.observer is None:
            raise ValueError('No observer given.')
        sun = self.observer.sun_altaz(Time.now())
        sun_10min = self.observer.sun_altaz(Time.now() + TimeDelta(10 * u.minute))
        self._twilight = FlatFielder.Twilight.DUSK \
            if sun_10min.alt.degree < sun.alt.degree else FlatFielder.Twilight.DAWN
        log.info('We are currently in %s twilight.', self._twilight.value)

        # do initial check
        if not self._initial_check():
            return

        # set binning
        if isinstance(camera, IBinning):
            log.info('Setting binning to %dx%d...', self._cur_binning[0], self._cur_binning[1])
            camera.set_binning(*self._cur_binning).wait()

        # get bias level
        self._bias_level = self._get_bias(camera)

        # move telescope
        future_track = self._pointing(telescope) if self._pointing is not None else None

        # get filter from first step and set it
        future_filter = Future[None](empty=True)
        if filters is not None and self._cur_filter is not None:
            log.info('Setting filter to %s...', self._cur_filter)
            future_filter = filters.set_filter(self._cur_filter)

        # wait for both
        Future.wait_all([future_track, future_filter])
        log.info('Finished initializing system.')

        # change stats
        log.info('Waiting for flat-field time...')
        self._state = FlatFielder.State.WAITING

    def _get_bias(self, camera: ICameraProxy) -> float:
        """Take bias image to determine bias level.

        Returns:
            Median bias level.
        """
        log.info('Taking BIAS image to determine median level...')

        # set full frame
        cam = camera
        if isinstance(camera, IWindow):
            full_frame = camera.get_full_frame().wait()
            camera.set_window(*full_frame).wait()

        # take image
        if isinstance(camera, IExposureTimeProxy):
            camera.set_exposure_time(0.)
        if isinstance(camera, IImageTypeProxy):
            camera.set_image_type(ImageType.BIAS)
        filename = cam.grab_image(broadcast=False).wait()

        # download image
        bias = self.vfs.read_image(filename)
        avg = float(np.median(bias.data))

        # return it
        log.info('Found median BIAS level of %.2f...', avg)
        return avg

    def _wait(self) -> None:
        """Wait for flat-field time."""

        # get solar elevation and evaluate function
        sun_alt, self._exptime = self._eval_function(Time.now())
        log.info('Calculated optimal exposure time of %.2fs in %dx%d at solar elevation of %.2f°.',
                 self._exptime, self._cur_binning[0], self._cur_binning[1], sun_alt)

        # then evaluate exposure time within a larger range
        state = self._eval_exptime(self._min_exptime * 0.5, self._max_exptime * 2.0)
        if state < 0:
            log.info('Sleeping a little...')
            self._abort.wait(10)
        elif state == 0:
            log.info('Starting to take test flat-fields...')
            self._state = FlatFielder.State.TESTING
        else:
            log.info('Missed flat-fielding time, finish task...')
            self._state = FlatFielder.State.FINISHED

    def _eval_function(self, time: Time) -> Tuple[float, float]:
        """Evaluate function for given filter at given time.

        Args:
            time: Time to evaluate function at.

        Returns:
            Estimated exposure time.
        """

        # get solar elevation and evaluate exptime
        if self.observer is None:
            raise ValueError('No observer given.')
        sun = self.observer.sun_altaz(time)
        exptime = self._eval(sun.alt.degree, binning=self._cur_binning, filter_name=self._cur_filter)

        # return solar altitude and exposure time
        return float(sun.alt.degree), exptime

    def _eval_exptime(self, min_exptime: Optional[float] = None, max_exptime: Optional[float] = None) -> int:
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
        if (self._twilight == FlatFielder.Twilight.DUSK and self._exptime > max_exptime) or \
           (self._twilight == FlatFielder.Twilight.DAWN and self._exptime < min_exptime):
            # in DUSK, if exptime is greater than max exptime, we're past flatfielding time
            # in DAWN, if exptime is less than min exptime, we're past flatfielding time
            return 1
        elif (self._twilight == FlatFielder.Twilight.DUSK and self._exptime < min_exptime) or \
             (self._twilight == FlatFielder.Twilight.DAWN and self._exptime > max_exptime):
            # in DUSK, if exptime is less than max exptime, we still need to wait
            # in DAWN, if exptime is greater than min exptime, we still need to wait
            return -1
        else:
            # otherwise it seems that we're in the middle of flat-fielding time
            return 0

    def _testing(self, camera: ICameraProxy) -> None:
        """Take flat-fields but don't store them."""

        # set window
        self._set_window(camera, testing=True)

        # do exposures, do not broadcast while testing
        log.info('Exposing test flat field for %.2fs...', self._exptime)
        cam = camera
        if isinstance(camera, IExposureTimeProxy):
            camera.set_exposure_time(float(self._exptime)).wait()
        if isinstance(camera, IImageTypeProxy):
            camera.set_image_type(ImageType.SKYFLAT)
        filename = cam.grab_image(broadcast=False).wait()

        # analyse image
        self._analyse_image(filename)

        # then evaluate exposure time
        state = self._eval_exptime()
        if state < 0:
            log.info('Sleeping a little...')
            self._abort.wait(10)
        elif state == 0:
            log.info('Starting to store flat-fields...')
            self._state = FlatFielder.State.RUNNING
        else:
            log.info('Missed flat-fielding time, finish task...')
            self._state = FlatFielder.State.FINISHED

    def _set_window(self, camera: Union[ICameraProxy, IExposureTimeProxy], testing: bool) -> None:
        """Set camera window.

        Args:
            testing: Whether we're in testing mode or not.
        """
        if isinstance(camera, IWindow):
            # get full frame
            left, top, width, height = camera.get_full_frame().wait()

            # if testing, take test frame, otherwise use full frame
            if testing:
                left, top, width, height = int(left + self._test_frame[0] / 100 * width),\
                                           int(top + self._test_frame[1] / 100 * width),\
                                           int(self._test_frame[2] / 100 * width),\
                                           int(self._test_frame[3] / 100 * height)

            # set it
            log.info('Setting camera window to %dx%d at %d,%d...', width, height, left, top)
            camera.set_window(left, top, width, height).wait()

    def _analyse_image(self, filename: str) -> bool:
        """Analyze image and return whether it's okay.

        Args:
            filename: Filename of image.

        Returns:
            Whether flat-field is okay.
        """

        # download image
        flat_field = self.vfs.read_image(filename)
        if flat_field is None:
            return False

        # get median from image
        self._median = self._get_image_median(flat_field, self._counts_frame)
        log.info('Got a flat field with median counts of %.2f.', self._median)

        # if count rate is too low, don't use this image to calculate new exposure time
        if self._median < self._min_counts:
            log.warning('Median counts (%d) too low, retrying last image with same exposure time...', self._median)
            return False

        else:
            # calculate deviation from target counts
            frac = abs(1. - self._median / self._target_count)

            # calculate new exposure time
            self._calc_new_exptime()

            # log and return
            if frac > self._target_count:
                log.warning('Deviation from target count (%.1f%%) is larger than allowed, retrying last image...', frac)
                return False
            else:
                log.info('Calculated new exposure time to be %.2fs.', self._exptime)
                return True

    @staticmethod
    def _get_image_median(image: Image, frame: Optional[Tuple[float, float, float, float]] = None) -> float:
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
        return float(np.median(data))

    def _calc_new_exptime(self) -> None:
        """Calculate new exposure time."""
        # calculate factor for new exposure time
        factor = (self._target_count - self._bias_level) / (self._median - self._bias_level)

        # limit factor to 0.1-10
        factor = min(10., max(0.1, factor))

        # calculate next exposure time
        self._exptime *= factor

    def _flat_field(self, telescope: ITelescopeProxy, camera: ICameraProxy) -> None:
        """Take flat-fields."""

        # set window
        self._set_window(camera, testing=False)

        # move telescope
        if self._pointing is not None:
            self._pointing(telescope).wait()

        # do exposures, do not broadcast while testing
        now = Time.now()
        log.info('Exposing flat field %d/%d for %.2fs...',
                 self._exposures_done + 1, self._exposures_total, self._exptime)
        if isinstance(camera, IExposureTimeProxy):
            camera.set_exposure_time(float(self._exptime)).wait()
        if isinstance(camera, IImageTypeProxy):
            camera.set_image_type(ImageType.SKYFLAT).wait()
        filename = camera.grab_image().wait()

        # analyse image
        if self._analyse_image(filename):
            # increase count and quite here, if finished
            self._exptime_done += self._exptime
            self._exposures_done += 1
            if self._exposures_done >= self._exposures_total:
                log.info('Finished all requested flat-fields..')
                self._state = FlatFielder.State.FINISHED
                return

            # call callback
            if self._callback is not None:
                if self.observer is None:
                    raise ValueError('No observer given.')
                sun = self.observer.sun_altaz(now)
                self._callback(datetime=now.isot, solalt=sun.alt.degree, exptime=self._exptime, counts=self._target_count,
                               filter=self._cur_filter, binning=self._cur_binning)

        # then evaluate exposure time
        state = self._eval_exptime()
        if state < 0:
            log.info('Going back to testing...')
            self._state = FlatFielder.State.TESTING
        elif state == 0:
            pass
        else:
            log.info('Missed flat-fielding time, finish task...')
            self._state = FlatFielder.State.FINISHED

    def abort(self) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ['FlatFielder']
