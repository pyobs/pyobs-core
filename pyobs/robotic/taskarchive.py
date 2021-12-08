import threading
from typing import Dict, Optional, Any, Type, List

from astroplan import Observer, ObservingBlock

from pyobs.comm import Comm
from pyobs.utils.time import Time
from pyobs.vfs import VirtualFileSystem
from .task import Task


class TaskArchive(object):
    def __init__(self, comm: Optional[Comm] = None, vfs: Optional[VirtualFileSystem] = None,
                 observer: Optional[Observer] = None, **kwargs: Any):
        self.comm = comm
        self.vfs = vfs
        self.observer = observer

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def _create_task(self, klass: Type[Task], **kwargs: Any) -> Task:
        return klass(**kwargs, tasks=self, comm=self.comm, vfs=self.vfs, observer=self.observer)

    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""
        raise NotImplementedError

    async def last_scheduled(self) -> Optional[Time]:
        """Returns time of last scheduler run."""
        raise NotImplementedError

    async def get_schedulable_blocks(self) -> List[ObservingBlock]:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """
        raise NotImplementedError

    async def update_schedule(self, blocks: List[Task], start_time: Time) -> None:
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """
        raise NotImplementedError

    async def get_pending_tasks(self, start_before: Time, end_after: Time, include_running: bool = True) -> Dict[str, Task]:
        """Fetch pending tasks from portal.

        Args:
            start_before: Task must start before this time.
            end_after: Task must end after this time.
            include_running: Whether to include a currently running task.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        raise NotImplementedError

    def get_task(self, time: Time) -> Optional[Task]:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        raise NotImplementedError

    async def run_task(self, task: Task, abort_event: threading.Event) -> bool:
        """Run a task.

        Args:
            task: Task to run
            abort_event: Abort event

        Returns:
            Success or not
        """
        raise NotImplementedError


__all__ = ['TaskArchive']
