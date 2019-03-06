import glob
import os
import importlib.util
import logging

from pytel.tasks import TaskFactoryBase, Task


log = logging.getLogger(__name__)


class ScriptTaskFactory(TaskFactoryBase):
    """A task factory that works on Python scripts in a given directory."""

    def __init__(self, path: str, *args, **kwargs):
        """Creates a new ScriptTask Factory.

        Args:
            path: Path to scripts.
        """
        TaskFactoryBase.__init__(self, *args, **kwargs)

        # store
        self._path = path
        self._tasks = {}

        # get list of tasks
        self.update_tasks()

    def update_tasks(self):
        """Update list of tasks."""

        # get all files in directory and loop them
        log.info('Updating script tasks in directory %s...', self._path)
        for filename in sorted(glob.glob(os.path.join(self._path, '*.py'))):
            # load module specs
            spec = importlib.util.spec_from_file_location('task', filename)

            # get module
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # __task__ given?
            if not hasattr(mod, '__task__'):
                log.warning('No __task__ found in %s.', filename)
                continue

            # does it inherit from Task?
            if not issubclass(mod.__task__, Task):
                raise ValueError('Task in %s is not of type "Task".', filename)

            # instantiate it
            task = self.create_task(mod.__task__)

            # get name and store it
            self._tasks[task.name()] = task

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


__all__ = ['ScriptTaskFactory']
