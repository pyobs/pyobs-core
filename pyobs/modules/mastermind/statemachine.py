import io
import logging

import yaml

from pyobs import PyObsModule, get_object
from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.interfaces import IFitsHeaderProvider
from pyobs.tasks import TaskFactory
from pyobs.utils.time import Time
from pyobs.tasks.state_machine.task import StateMachineTask

log = logging.getLogger(__name__)


class StateMachineMastermind(PyObsModule, IFitsHeaderProvider):
    """Mastermind that acts as a state machine."""

    def __init__(self, tasks: dict, *args, **kwargs):
        """Initialize a new auto focus system."""
        PyObsModule.__init__(self, thread_funcs=self._run_thread, *args, **kwargs)

        # storage for data
        self._task_factory: TaskFactory = get_object(tasks, comm=self.comm, observer=self.observer, vfs=self.vfs,
                                                     closing_event=self.closing)

        # observation name and exposure number
        self._task = None
        self._obs = None
        self._exp = None

        # roof
        self._roof_open = False

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(RoofOpenedEvent, self._on_roof_opened)
            self.comm.register_event(RoofClosingEvent, self._on_roof_closing)

    def _run_thread(self):
        # wait a little
        self.closing.wait(1)

        # run until closed
        while not self.closing.is_set():
            # get now
            now = Time.now()

            # find task that we want to run now
            for name in self._task_factory.list():
                # get task
                task: StateMachineTask = self._task_factory.get(name)

                # is it observable?
                if task.is_observable(now):
                    log.info('Task found: %s.', name)
                    self._task = task
                    break

            else:
                # no task found
                self.closing.wait(10)
                continue

            # create obs
            self._obs = self._create_obs_name()
            self._exp = 0

            # send event
            self.comm.send_event(TaskStartedEvent(self._task.name, self._obs))

            # run task
            log.info('Running task %s for observation %s...', self._task.name, self._obs)
            while self._task.is_observable(Time.now()):
                self._task(self.closing)

            # finish
            self._obs = None
            self._exp = None

            # send event
            self.comm.send_event(TaskFinishedEvent(self._task.name, self._obs))

    def _create_obs_name(self):
        """Create a new unique observation name."""

        # read file with last observation config
        try:
            # read file
            with self.vfs.open_file('/pyobs/observation.yaml', 'r') as f:
                obs = yaml.load(f, yaml.FullLoader)
        except FileNotFoundError:
            obs = None

        # check
        if obs is None or 'night' not in obs or 'number' not in obs:
            obs = {'night': None, 'number': 0}

        # get current night
        night = Time.now().night_obs(self.observer).strftime('%Y%m%d')

        # same night or not?
        if obs['night'] == night:
            # same night, so increase number
            obs['number'] += 1
        else:
            # new night, start fresh
            obs = {'night': night, 'number': 0}

        # write new observation config
        with self.vfs.open_file('/pyobs/observation.yaml', 'w') as f:
            with io.StringIO() as sio:
                yaml.dump(obs, sio)
                f.write(bytes(sio.getvalue(), 'utf8'))

        # create obs name and return it
        return '{night:s}-{number:04d}'.format(**obs)

    def get_fits_headers(self, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        # inside an observation?
        if self._task is not None:
            hdr = self._task.get_fits_headers()
            hdr['OBS'] = self._obs, 'Name of observation'
            hdr['TASK'] = self._task.name, 'Name of task'
            return hdr
        else:
            return {}

    def _on_roof_opened(self, event: RoofOpenedEvent, sender: str, *args, **kwargs):
        """Roof has opened.

        Args:
            event: The event.
            sender: Who sent it.
        """

        log.warning('Received event that roof has opened.')
        self._roof_open = True

    def _on_roof_closing(self, event: RoofClosingEvent, sender: str, *args, **kwargs):
        """Roof is closing.

        Args:
            event: The event.
            sender: Who sent it.
        """

        log.warning('Received event that roof is closing.')
        self._roof_open = False


__all__ = ['StateMachineMastermind']
