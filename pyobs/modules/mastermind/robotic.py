import logging
import threading
from typing import Union
import astropy.units as u

from pyobs import Module, get_object
from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.interfaces import IFitsHeaderProvider, IAutonomous
from pyobs.robotic.taskarchive import TaskArchive
from pyobs.robotic.task import Task
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class RoboticMastermind(Module, IAutonomous, IFitsHeaderProvider):
    """Mastermind for a full robotic mode."""

    def __init__(self, tasks: Union[TaskArchive, dict], allowed_late_start: int = 300, allowed_overrun: int = 300,
                 *args, **kwargs):
        """Initialize a new auto focus system.

        Args:
            tasks: Task archive to use
            allowed_late_start: Allowed seconds to start late.
            allowed_overrun: Allowed time for a task to exceed it's window in seconds
        """
        Module.__init__(self, *args, **kwargs)

        # store
        self._allowed_late_start = allowed_late_start
        self._allowed_overrun = allowed_overrun
        self._running = False

        # add thread func
        self._add_thread_func(self._run_thread, True)

        # get task archive
        self._task_archive: TaskArchive = get_object(tasks, object_class=TaskArchive,
                                                     comm=self.comm, vfs=self.vfs, observer=self.observer)

        # observation name and exposure number
        self._task = None
        self._obs = None
        self._exp = None

    def open(self):
        """Open module."""
        Module.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(TaskStartedEvent)
            self.comm.register_event(TaskFinishedEvent)

        # start
        self._running = True

        # open scheduler
        self._task_archive.open()

    def close(self):
        """Close module."""
        Module.close(self)

        # close scheduler
        self._task_archive.close()

    def start(self, *args, **kwargs):
        """Starts a service."""
        log.info('Starting robotic system...')
        self._running = True

    def stop(self, *args, **kwargs):
        """Stops a service."""
        log.info('Stopping robotic system...')
        self._running = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running."""
        return self._running

    def _run_thread(self):
        # wait a little
        self.closing.wait(1)

        # flags
        first_late_start_warning = True

        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._running:
                # sleep a little and continue
                self.closing.wait(1)
                continue

            # get now
            now = Time.now()

            # find task that we want to run now
            task: Task = self._task_archive.get_task(now)
            if task is None or not task.can_run():
                # no task found
                self.closing.wait(10)
                continue

            # starting too late?
            if not task.can_start_late:
                late_start = now - task.start
                if late_start > self._allowed_late_start * u.second:
                    # only warn once
                    if first_late_start_warning:
                        log.warning('Time since start of window (%.1f) too long (>%.1f), skipping task...',
                                    late_start.to_value('second'), self._allowed_late_start)
                    first_late_start_warning = False

                    # sleep a little and skip
                    self.closing.wait(10)
                    continue

            # reset warning
            first_late_start_warning = True

            # set it
            self._task = task

            # ETA
            eta = now + self._task.duration * u.second

            # send event
            self.comm.send_event(TaskStartedEvent(name=self._task.name, id=self._task.id, eta=eta))

            # run task in thread
            log.info('Running task %s...', self._task.name)
            abort_event = threading.Event()
            task_thread = threading.Thread(target=self._task_archive.run_task, args=(self._task, abort_event))
            task_thread.start()

            # wait for it
            while True:
                # not alive anymore?
                if not task_thread.is_alive():
                    # finished
                    break

                # closing?
                if self.closing.is_set() or Time.now() > window[1] + self._allowed_overrun * u.second:
                    # set event and wait for thread
                    abort_event.set()
                    task_thread.join()
                    break

                # just sleep a little and wait
                self.closing.wait(10)

            # send event
            self.comm.send_event(TaskFinishedEvent(name=self._task.name, id=self._task.id))

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
