import glob
import os

from pytel.tasks import TaskFactoryBase, Task
from .task import ScriptTask


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

    def list(self) -> list:
        """List all tasks from this factory.

        Returns:
            List of all tasks.
        """

        # get all files in directory
        files = sorted(glob.glob(os.path.join(self._path, '*.py')))

        # get basenames and script extensions
        return [os.path.splitext(os.path.basename(f))[0] for f in files]

    def get(self, name: str) -> Task:
        """Returns a single task from the factory.

        Args:
            name: Name of task

        Returns:
            The task object.

        Raises:
            ValueError: If task with given name does not exist.
        """

        # build full filename
        filename = os.path.join(self._path, name + '.py')

        # does it exist?
        if not os.path.exists(filename):
            raise ValueError('Task of given name does not exist.')

        # return task
        return self.create_task(ScriptTask, filename)


__all__ = ['ScriptTaskFactory']
