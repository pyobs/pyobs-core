import logging

from pyobs import PyObsModule, get_object
from pyobs.tasks import TaskFactory
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class StateMachineMastermind(PyObsModule):
    """Mastermind that acts as a state machine."""

    def __init__(self, tasks: dict, *args, **kwargs):
        """Initialize a new auto focus system."""
        PyObsModule.__init__(self, *args, **kwargs)

        # storage for data
        self._task_factory: TaskFactory = get_object(tasks, comm=self.comm, observer=self.observer, vfs=self.vfs)

    def run(self):
        # wait a little
        self.closing.wait(1)

        # run until closed
        while not self.closing.is_set():
            # current task
            cur_task = None

            # find task that we want to run now
            for name in self._task_factory.list():
                task = self._task_factory.get(name)
                if Time.now() in task:
                    log.info('Task found: %s.', name)
                    cur_task = task
                    break
            else:
                # no task found
                self.closing.wait(10)
                continue

            # init task
            log.info('Initializing task...')
            cur_task.start()

            # steps
            log.info('Performing task steps...')
            while Time.now() in cur_task:
                 cur_task()

            # finish
            log.info('Shutting down task...')
            cur_task.stop()


__all__ = ['StateMachineMastermind']
