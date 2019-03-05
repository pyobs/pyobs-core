import logging

from pytel.tasks import Task


log = logging.getLogger(__name__)


class ScriptTask(Task):
    """A task based on a Python script."""

    def __init__(self, filename: str, *args, **kwargs):
        """Initialize a new script task.

        Args:
            filename: Name of file to use as script.
        """
        Task.__init__(self, *args, **kwargs)

        # load script
        with open(filename, 'r') as f:
            self._script = f.read()

    def __call__(self):
        """Run the task."""

        # define scope
        scope = {
            'comm': self.comm,
            'environment': self.environment,
            'vfs': self.vfs,
            'log': log
        }

        # execute it
        try:
            exec(self._script, scope)
        except:
            log.exception("Error during execution of task:")


__all__ = ['ScriptTask']
