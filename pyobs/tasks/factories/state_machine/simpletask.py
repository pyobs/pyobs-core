from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.interfaces import ITelescope, IFocuser, ICamera
from pyobs.utils.time import Time
from .task import StateMachineTask


class SimpleStateMachineTask(StateMachineTask):
    """A simple task for the state machine."""

    def __init__(self, ra=None, dec=None, steps=None, telescope=None, camera=None, *args, **kwargs):
        """Initializes a new Task.

        Args:
            ra: RA of target.
            dec: Dec of target.
            steps: List of dictionaries describing step, must contain "filter" and "exptime" and "count".
            telescope:
            camera:
        """
        StateMachineTask.__init__(self, *args, **kwargs)

        # store
        self._coords = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')
        self._steps = steps
        self._cur_step = 0

        # telescope and camera
        self._telescope_name = telescope
        self._telescope = None
        self._camera_name = camera
        self._camera = None

    def __contains__(self, time: Time):
        """Whether the given time is in the interval of this task."""
        return self._start <= time < self._end

    def start(self):
        """Initial steps for a task."""

        # get telescope and camera
        self._telescope = self.comm[self._telescope_name]   # type: (ITelescope, IFocuser)
        self._camera = self.comm[self._camera_name]         # type: ICamera

        # move telescope
        self._telescope.track(self._coords.ra.degree, self._coords.dec.degree)

        # get filter from first step and set it
        self._cur_step = 0
        self._telescope.set_filter(self._steps[self._cur_step]['filter'])

    def __call__(self):
        """Do a step in the task."""

        # get step
        step = self._steps[self._cur_step]

        # set filter
        self._telescope.set_filter(step['filter'])

        # do exposures
        self._camera.expose(exposure_time=step['exptime'], image_type=ICamera.ImageType.OBJECT, count=step['count'])

        # go to next step
        self._cur_step += 1
        if self._cur_step >= len(self._steps):
            self._cur_step = 0

    def stop(self):
        """Final steps for a task."""

        # stop telescope
        self._telescope.stop_motion()

        # release proxies
        self._telescope = None
        self._camera = None


__all__ = ['SimpleStateMachineTask']
