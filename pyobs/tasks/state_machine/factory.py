import logging
import yaml
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.tasks import TaskFactoryBase, Task
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class StateMachineTaskFactory(TaskFactoryBase):
    """A task factory that works as a state machine."""

    def __init__(self, filename, *args, **kwargs):
        """Creates a new StateMachineTask Factory."""
        TaskFactoryBase.__init__(self, *args, **kwargs)

        # store
        self._tasks = {}
        self._filename = filename
        self._last_update = None

        # get list of tasks
        self._check_update()

    def update_tasks(self):
        """Update list of tasks."""
        with self.vfs.open_file(self._filename, 'r') as f:
            # load yaml
            tasks = yaml.load(f, Loader=yaml.FullLoader)

            # create tasks
            self._tasks = {k: self.create_task(k, v['class'], **v) for k, v in tasks.items()}
            log.info('Found %d task(s).', len(self._tasks))

    def _check_update(self):
        """Regularly update task list."""

        # update necessary?
        if self._last_update is None or (Time.now() - self._last_update) > TimeDelta(1. * u.hour):
            # do update
            self.update_tasks()

            # set time
            self._last_update = Time.now()

    def list(self) -> list:
        """List all tasks from this factory.

        Returns:
            List of all tasks.
        """

        # need to update tasks?
        self._check_update()

        # return all task names
        return sorted(self._tasks.keys())

    def get(self, name: str) -> Task:
        """Returns a single task from the factory.

        Args:
            name: Name of task

        Returns:
            The task object.

        Raises:
            ValueError: If task with given name does not exist.
        """

        # need to update tasks?
        self._check_update()

        # does it exist?
        if name not in self._tasks:
            raise ValueError('Task of given name does not exist.')

        # return it
        return self._tasks[name]


__all__ = ['StateMachineTaskFactory']
