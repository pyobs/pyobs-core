from typing import Tuple

from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

from pyobs.interfaces import ITelescope, IFocuser, ICamera, IFilters
from pyobs.utils.threads import Future
from pyobs.utils.time import Time
from .task import StateMachineTask


log = logging.getLogger(__name__)


class CalibTask(StateMachineTask):
    """A calibration task for the state machine."""

    def __init__(self, binning: Tuple = (1, 1), exptime: float = 0, camera: str = None,
                 *args, **kwargs):
        """Initializes a new Task.

        Args:
            binning: Binning for calibration.
            exptime: Exposure time.
            camera: Name of ICamera module to use.
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._binning = binning
        self._exptime = exptime

        # camera
        self._camera_name = camera
        self._camera = None

    def start(self):
        """Initial steps for a task."""

        # get camera
        self._camera: ICamera = self.comm[self._camera_name]

    def __call__(self):
        """Do a step in the task."""

        # get image type
        img_type = ICamera.ImageType.BIAS if self._exptime == 0 else ICamera.ImageType.DARK

        # do exposure
        log.info('Exposing %s image(s) for %.2fs...', img_type.value, self._exptime)
        self._camera.expose(exposure_time=self._exptime * 1000., image_type=img_type).wait()

    def stop(self):
        """Final steps for a task."""

        # release proxies
        self._camera = None

        # finished
        log.info('Finished task.')


__all__ = ['CalibTask']
