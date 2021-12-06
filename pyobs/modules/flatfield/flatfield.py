import logging
import threading
from enum import Enum
from typing import Union, Tuple, List, Optional, Any, Dict

from pyobs.events import BadWeatherEvent, RoofClosingEvent, Event
from pyobs.interfaces import IFlatField, IFilters, IBinning
from pyobs.interfaces import IFiltersProxy, ICameraProxy, ITelescopeProxy, IBinning
from pyobs.modules import Module
from pyobs.object import get_object
from pyobs.modules import timeout
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.skyflats import FlatFielder

log = logging.getLogger(__name__)


class FlatFielderProxy:
    pass


class FlatField(Module, IFlatField, IBinning, IFilters):
    """Module for auto-focusing a telescope."""
    __module__ = 'pyobs.modules.flatfield'

    class Twilight(Enum):
        DUSK = 'dusk'
        DAWN = 'dawn'

    class State(Enum):
        INIT = 'init'
        WAITING = 'waiting'
        TESTING = 'testing'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, telescope: Union[str, ITelescopeProxy], camera: Union[str, ICameraProxy],
                 flat_fielder: Optional[Union[Dict[str, Any], FlatFielder]],
                 filters: Optional[Union[str, IFiltersProxy]] = None, log_file: Optional[str] = None, **kwargs: Any):
        """Initialize a new flat fielder.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            flat_fielder: Flat field object to use.
            filters: Name of IFilters, if any.
            log_file: Name of file to store flat field log in.
        """
        Module.__init__(self, **kwargs)

        # store telescope, camera, and filters
        self._telescope = telescope
        self._camera = camera
        self._filter_wheel = filters
        self._abort = threading.Event()

        # flat fielder
        self._flat_fielder = self.get_object(flat_fielder, FlatFielder, callback=self.callback)

        # init log file
        self._publisher = None if log_file is None else CsvPublisher(log_file)

        # init binning and filter
        self._binning = (1, 1)
        self._filter: Optional[str] = None

        # need to add IFilters interface?
        if self._filter_wheel is not None:
            # check filters
            if not self._flat_fielder.has_filters:
                raise ValueError('Filter wheel module given in config, but no filters in functions.')

            # add it
            #self.__class__ = type('FlatFieldFilter', (FlatField, IFilters), {})

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # check telescope, camera, and filters
        try:
            self.proxy(self._telescope, ITelescopeProxy)
            self.proxy(self._camera, ICameraProxy)
            self.proxy(self._filter_wheel, IFiltersProxy)
        except ValueError:
            log.warning('Either telescope, camera or filters do not exist or are not of correct type at the moment.')

            # subscribe to events
            if self.comm:
                await self.comm.register_event(BadWeatherEvent, self._abort_weather)
                await self.comm.register_event(RoofClosingEvent, self._abort_weather)

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)
        self._abort.set()

    def callback(self, datetime: str, solalt: float, exptime: float, counts: float, filter: str,
                 binning: Tuple[int, int]) -> None:
        """Callback for flat-field class to call with statistics."""
        # write log
        if self._publisher is not None:
            self._publisher(datetime=datetime, solalt=solalt, exptime=exptime, counts=counts,
                            filter=filter, binning=binning[0])

    def list_binnings(self, **kwargs: Any) -> List[Tuple[int, int]]:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """
        return self.proxy(self._camera, IBinning).list_binnings().wait()

    def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        self._binning = (x, y)

    def get_binning(self, **kwargs: Any) -> Tuple[int, int]:
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        return self._binning

    def list_filters(self, **kwargs: Any) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        return self.proxy(self._filter_wheel, IFiltersProxy).list_filters().wait()

    def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If binning could not be set.
        """
        self._filter = filter_name

    def get_filter(self, **kwargs: Any) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        return '' if self._filter is None else self._filter

    @timeout(3600)
    def flat_field(self, count: int = 20, **kwargs: Any) -> Tuple[int, float]:
        """Do a series of flat fields in the given filter.

        Args:
            count: Number of images to take

        Returns:
            Number of images actually taken and total exposure time in ms
        """
        log.info('Performing flat fielding...')
        self._abort = threading.Event()

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescopeProxy = self.proxy(self._telescope, ITelescopeProxy)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICameraProxy = self.proxy(self._camera, ICameraProxy)

        # get filter wheel
        filters: Optional[IFiltersProxy] = None
        if self._filter_wheel is not None:
            log.info('Getting proxy for filter wheel...')
            filters = self.proxy(self._filter_wheel, IFiltersProxy)

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
            state = self._flat_fielder(telescope, camera, count=count, binning=self._binning,
                                       filters=filters, filter_name=self._filter)

        # stop telescope
        log.info('Stopping telescope...')
        telescope.stop_motion().wait()
        log.info('Flat-fielding finished.')

        # return number of taken images
        return int(self._flat_fielder.image_count), float(self._flat_fielder.total_exptime)

    @timeout(20)
    def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()

    def _abort_weather(self, event: Event, sender: str, **kwargs: Any) -> bool:
        """Abort on bad weather."""
        self.abort()
        return True


__all__ = ['FlatField']
