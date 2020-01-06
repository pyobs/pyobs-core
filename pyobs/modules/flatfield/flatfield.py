import logging
import threading
import typing
from enum import Enum

from pyobs.events import BadWeatherEvent, RoofClosingEvent, Event
from pyobs.interfaces import ICamera, IFlatField, IFilters, ITelescope, IMotion
from pyobs import PyObsModule, get_object
from pyobs.modules import timeout
from pyobs.utils.skyflats.flatfielder import FlatFielder

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
                 filters: typing.Union[str, IFilters], flat_fielder: typing.Union[dict, FlatFielder],
                 *args, **kwargs):
        """Initialize a new flat fielder.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            filters: Name of IFilters, if any.
            pointing: Pointing to use.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope, camera, and filters
        self._telescope = telescope
        self._camera = camera
        self._filters = filters
        self._flat_fielder: FlatFielder = get_object(flat_fielder, FlatFielder, observer=self.observer, vfs=self.vfs)
        self._abort = threading.Event()

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

            # subscribe to events
            if self.comm:
                self.comm.register_event(BadWeatherEvent, self._abort_weather)
                self.comm.register_event(RoofClosingEvent, self._abort_weather)

    def close(self):
        """Close module."""
        PyObsModule.close(self)
        self._abort.set()

    @timeout(3600000)
    def flat_field(self, filter_name: str, count: int = 20, binning: int = 1, *args, **kwargs) -> (int, int):
        """Do a series of flat fields in the given filter.

        Args:
            filter_name: Name of filter
            count: Number of images to take
            binning: Binning to use

        Returns:
            Number of images actually taken and total exposure time in ms
        """
        log.info('Performing flat fielding...')

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, ICamera)

        # get filter wheel
        log.info('Getting proxy for filter wheel...')
        filters: IFilters = self.proxy(self._filters, IFilters)

        # reset
        self._flat_fielder.reset()

        # run until state is finished or we aborted
        state = None
        while state != FlatFielder.State.FINISHED:
            # can we run?
            if not telescope.is_ready().wait():
                log.error('Telescope not in valid state, aborting...')
                return self._flat_fielder.image_count, self._flat_fielder.total_exptime
            if self._abort.is_set():
                log.warning('Aborting flat-fielding...')
                return self._flat_fielder.image_count, self._flat_fielder.total_exptime

            # do step
            state = self._flat_fielder(telescope, camera, filters, filter_name, count, binning)

        # stop telescope
        log.info('Stopping telescope...')
        telescope.stop_motion().wait()
        log.info('Flat-fielding finished.')

        # return number of taken images
        return self._flat_fielder.image_count, self._flat_fielder.total_exptime

    @timeout(20000)
    def abort(self, *args, **kwargs):
        """Abort current actions."""
        self._abort.set()

    def flat_field_status(self, *args, **kwargs) -> dict:
        """Returns current status of auto focus.

        Returned dictionary contains a list of focus/fwhm pairs in X and Y direction.

        Returns:
            Dictionary with current status.
        """
        raise NotImplementedError

    def _abort_weather(self, event: Event, sender: str, *args, **kwargs):
        """Abort on bad weather."""
        self.abort()


__all__ = ['FlatField']
