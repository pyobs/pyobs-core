import logging
import yaml

from pyobs import get_object
from pyobs.tasks import TaskFactoryBase, Task


log = logging.getLogger(__name__)


class StateMachineTaskFactory(TaskFactoryBase):
    """A task factory that works as a state machine."""

    def __init__(self, filename, *args, **kwargs):
        """Creates a new StateMachineTask Factory."""
        TaskFactoryBase.__init__(self, *args, **kwargs)

        # store
        self._tasks = {}
        self._filename = filename

        # get list of tasks
        self.update_tasks()

    def update_tasks(self):
        """Update list of tasks."""
        with self.vfs.open_file(self._filename, 'r') as f:
            # load yaml
            tasks = yaml.load(f, Loader=yaml.FullLoader)

            # create tasks
            self._tasks = {k: self.create_task(v['class'], **v) for k, v in tasks.items()}
            log.info('Found %d tasks.', len(self._tasks))

    def list(self) -> list:
        """List all tasks from this factory.

        Returns:
            List of all tasks.
        """

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

        # does it exist?
        if name not in self._tasks:
            raise ValueError('Task of given name does not exist.')

        # return it
        return self._tasks[name]


__all__ = ['StateMachineTaskFactory']
