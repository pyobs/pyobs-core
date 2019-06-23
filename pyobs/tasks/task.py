import threading
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.vfs import VirtualFileSystem


class Task:
    """Base class for all tasks in the system."""

    def __init__(self, name: str = None, comm: Comm = None, observer: Observer = None,
                 vfs: VirtualFileSystem = None, *args, **kwargs):
        """Initializes a new Task.

        Args:
            name: Name of task.
            comm: Comm object for communicating with other modules.
            observer: The observer to use
            vfs: Virtual File System to use.
        """

        # store variables
        self.name = name
        self.comm = comm
        self.observer = observer
        self.vfs = vfs

    def __call__(self, closing_event: threading.Event):
        """Run the task.

        Args:
            closing_event: Event to be set when task should close.
        """
        raise NotImplementedError


__all__ = ['Task']
