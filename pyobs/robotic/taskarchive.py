import threading
from typing import Dict

from astroplan import Observer

from pyobs.comm import Comm
from pyobs.utils.time import Time
from pyobs.vfs import VirtualFileSystem
from .task import Task


class TaskArchive:
    def __init__(self, comm: Comm = None, vfs: VirtualFileSystem = None, observer: Observer = None, *args, **kwargs):
        self.comm = comm
        self.vfs = vfs
        self.observer = observer

    def open(self):
        pass

    def close(self):
        pass

    def _create_task(self, klass, *args, **kwargs):
        return klass(*args, **kwargs, tasks=self, comm=self.comm, vfs=self.vfs, observer=self.observer)

    def last_changed(self) -> Time:
        """Returns time when last time any blocks changed."""
        raise NotImplementedError

    def last_scheduled(self) -> Time:
        """Returns time of last scheduler run."""
        raise NotImplementedError

    def get_schedulable_blocks(self) -> list:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """
        raise NotImplementedError

    def update_schedule(self, blocks: list, start_time: Time):
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """
        raise NotImplementedError

    def get_pending_tasks(self, start_before: Time, end_after: Time, include_running: bool = True) -> Dict[str, Task]:
        """Fetch pending tasks from portal.

        Args:
            start_before: Task must start before this time.
            end_after: Task must end after this time.
            include_running: Whether to include a currently running task.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout if request timed out.
            ValueError if something goes wrong.
        """
        raise NotImplementedError

    def get_task(self, time: Time) -> Task:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        raise NotImplementedError

    def run_task(self, task: Task, abort_event: threading.Event):
        """Run a task.

        Args:
            task: Task to run
            abort_event: Abort event

        Returns:
            Success or not
        """
        raise NotImplementedError


__all__ = ['TaskArchive']
