import logging
import threading
from typing import Union

from pyobs import PyObsModule, get_object
from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.interfaces import IFitsHeaderProvider
from pyobs.robotic.scheduler import Scheduler
from pyobs.robotic.task import Task
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class RoboticMastermind(PyObsModule, IFitsHeaderProvider):
    """Mastermind for a full robotic mode."""

    def __init__(self, scheduler: Union[Scheduler, dict], *args, **kwargs):
        """Initialize a new auto focus system."""
        PyObsModule.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._run_thread, True)

        # get scheduler
        self._scheduler: Scheduler = get_object(scheduler, object_class=Scheduler,
                                                comm=self.comm, vfs=self.vfs, observer=self.observer)

        # observation name and exposure number
        self._task = None
        self._obs = None
        self._exp = None

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # open scheduler
        self._scheduler.open()

    def close(self):
        """Close module."""
        PyObsModule.close(self)

        # close scheduler
        self._scheduler.close()

    def _run_thread(self):
        # wait a little
        self.closing.wait(1)

        # run until closed
        while not self.closing.is_set():
            # get now
            now = Time.now()

            # find task that we want to run now
            task: Task = self._scheduler.get_task(now)
            if task is None or not task.can_run():
                # no task found
                self.closing.wait(10)
                continue

            # set it
            self._task = task

            # task window
            window = self._task.window()

            # send event
            self.comm.send_event(TaskStartedEvent(self._task.name))

            # run task in thread
            log.info('Running task %s...', self._task.name)
            abort_event = threading.Event()
            task_thread = threading.Thread(target=self._scheduler.run_task, args=(self._task, abort_event))
            task_thread.start()

            # wait for it
            while True:
                # not alive anymore?
                if not task_thread.is_alive():
                    # finished
                    break

                # time over or closing?
                if self.closing.is_set() or Time.now() > window[1]:
                    # set event and wait for thread
                    abort_event.set()
                    task_thread.join()
                    break

                # just sleep a little and wait
                self.closing.wait(10)

            # send event
            self.comm.send_event(TaskFinishedEvent(self._task.name))

            # finish
            log.info('Finished task %s.', self._task.name)
            self._task = None

    def get_fits_headers(self, namespaces: list = None, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # inside an observation?
        if self._task is not None:
            hdr = self._task.get_fits_headers()
            hdr['TASK'] = self._task.name, 'Name of task'
            hdr['REQNUM'] = str(self._task.id), 'Unique ID of task'
            return hdr
        else:
            return {}


__all__ = ['RoboticMastermind']
