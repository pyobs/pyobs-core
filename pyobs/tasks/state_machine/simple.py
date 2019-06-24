import threading
from enum import Enum

from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

from pyobs.interfaces import ITelescope, ICamera, IFilters
from pyobs.utils.threads import Future
from .task import StateMachineTask


log = logging.getLogger(__name__)


class SimpleStateMachineTask(StateMachineTask):
    """A simple task for the state machine."""

    class State(Enum):
        INIT = 'init'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, ra: float = None, dec: float = None, steps: list = None, telescope: str = None,
                 camera: str = None, filters: str = None, *args, **kwargs):
        """Initializes a new Task.

        Args:
            ra: RA of target.
            dec: Dec of target.
            steps: List of dictionaries describing step containing:
                - filter: Filter to use
                - exptime: Exposure time in sec
                - count: Number of images to take (default: 1)
                - type: Image type object/bias/dark (default: object)
            telescope: Name of ITelescope module to use.
            camera: Name of ICamera module to use.
            filters: Name of IFilters module to use.
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._coords = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')
        self._steps = steps
        self._cur_step = 0
        self._exposures_left = 0

        # state machine
        self._state = SimpleStateMachineTask.State.INIT

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
        if self._state == SimpleStateMachineTask.State.INIT:
            # init task
            self._init(closing_event)
        elif self._state == SimpleStateMachineTask.State.RUNNING:
            # take images
            self._step(closing_event)
        else:
            # wait
            closing_event.wait(10)

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

        # move telescope
        log.info('Moving telescope to %s...', self._coords.to_string('hmsdms'))
        future_track = self._telescope.track(self._coords.ra.degree, self._coords.dec.degree)

        # get filter from first step and set it
        self._cur_step = 0
        step = self._steps[self._cur_step]
        log.info('Setting filter to %s...', step['filter'])
        future_filter = self._filters.set_filter(step['filter'])

        # number of exposures
        self._exposures_left = step['count'] if 'count' in step else 1

        # wait for both
        Future.wait_all([future_track, future_filter])

        # change state
        self._state = SimpleStateMachineTask.State.RUNNING

    def _step(self, closing_event: threading.Event):
        """Single step for a task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # get step
        step = self._steps[self._cur_step]
        img_type = ICamera.ImageType(step['type'].lower()) if 'type' in step else ICamera.ImageType.OBJECT

        # do exposures
        log.info('Exposing %s image for %.2fs...', img_type.value, step['exptime'])
        self._camera.expose(exposure_time=step['exptime'] * 1000., image_type=img_type).wait()
        self._exposure += 1
        self._exposures_left -= 1

        # exposures left?
        if self._exposures_left == 0:
            # remember filter
            old_filter = step['filter']

            # go to next step
            self._cur_step += 1
            if self._cur_step >= len(self._steps):
                # go back to first step
                self._cur_step = 0

            # get step
            step = self._steps[self._cur_step]

            # set exposures left
            self._exposures_left = step['count'] if 'count' in step else 1

            # set filter
            if old_filter != step['filter']:
                log.info('Setting filter to %s...', step['filter'])
                self._telescope.set_filter(step['filter']).wait()

    def finish(self):
        """Final steps for a task."""

        # already finished?
        if self._state == SimpleStateMachineTask.State.FINISHED:
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
        self._state = SimpleStateMachineTask.State.FINISHED


__all__ = ['SimpleStateMachineTask']
