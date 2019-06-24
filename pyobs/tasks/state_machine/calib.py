import threading
from enum import Enum
from typing import Tuple
import logging

from pyobs.interfaces import ICamera
from .task import StateMachineTask


log = logging.getLogger(__name__)


class CalibTask(StateMachineTask):
    """A calibration task for the state machine."""

    class State(Enum):
        INIT = 'init'
        RUNNING = 'running'
        FINISHED = 'finished'

    def __init__(self, binning: Tuple = (1, 1), exptime: float = 0, count: int = None, camera: str = None,
                 *args, **kwargs):
        """Initializes a new Task.

        Args:
            binning: Binning for calibration.
            exptime: Exposure time.
            count: Number of images to take.
            camera: Name of ICamera module to use.
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._binning = binning
        self._exptime = exptime
        self._count = count
        self._exposures_left = None

        # state machine
        self._state = CalibTask.State.INIT

        # camera
        self._camera_name = camera
        self._camera = None

    def __call__(self, closing_event: threading.Event, *args, **kwargs):
        """Run the task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # which state?
        if self._state == CalibTask.State.INIT:
            # init task
            self._init()
        elif self._state == CalibTask.State.RUNNING:
            # take calib frames
            self._step()
        else:
            # wait
            closing_event.wait(10)

    def _init(self):
        """Init task."""

        # get camera
        self._camera: ICamera = self.comm[self._camera_name]

        # set exposures
        self._exposures_left = self._count
        self._exposures = 0

        # change state
        self._state = CalibTask.State.RUNNING

    def _step(self):
        """Single step for a task."""

        # get image type
        img_type = ICamera.ImageType.BIAS if self._exptime == 0 else ICamera.ImageType.DARK

        # do exposure
        log.info('Exposing %s image(s) for %.2fs...', img_type.value, self._exptime)
        self._camera.expose(exposure_time=self._exptime * 1000., image_type=img_type).wait()
        self._exposure += 1

        # decrease exposure count and finish, if necessary
        self._exposures_left -= 1
        if self._exposures_left == 0:
            self.finish()

    def finish(self):
        """Final steps for a task."""

        # already finished?
        if self._state == CalibTask.State.FINISHED:
            return

        # release proxies
        self._camera = None

        # finished
        log.info('Finished task.')

        # change state
        self._state = CalibTask.State.FINISHED


__all__ = ['CalibTask']
