import io
import logging

import yaml

from pyobs import PyObsModule, get_object
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
        PyObsModule.__init__(self, *args, **kwargs)

        # storage for data
        self._task_factory: TaskFactory = get_object(tasks, comm=self.comm, observer=self.observer, vfs=self.vfs,
                                                     closing_event=self.closing)

        # observation name and exposure number
        self._task = None
        self._obs = None
        self._exp = None

    def run(self):
        # wait a little
        self.closing.wait(1)

        # run until closed
        while not self.closing.is_set():
            # find task that we want to run now
            for name in self._task_factory.list():
                task: StateMachineTask = self._task_factory.get(name)
                if Time.now() in task:
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
            while Time.now() in self._task:
                # do task step
                self._task(self.closing)

            # finish
            log.info('Shutting down task...')
            self._task.finish()
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
            return {
                'OBS': (self._obs, 'Name of observation'),
                'EXP': (self._exp, 'Number of exposure within observation'),
                'TASK': (self._task.name, 'Name of task')
            }
        else:
            return {}


__all__ = ['StateMachineMastermind']
