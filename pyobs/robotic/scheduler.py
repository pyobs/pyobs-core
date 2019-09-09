from astroplan import Observer

from pyobs.comm import Comm
from pyobs.utils.time import Time
from pyobs.vfs import VirtualFileSystem
from .task import Task


class Scheduler:
    def __init__(self, comm: Comm = None, vfs: VirtualFileSystem = None, observer: Observer = None, *args, **kwargs):
        self.comm = comm
        self.vfs = vfs
        self.observer = observer

    def open(self):
        pass

    def close(self):
        pass

    def get_task(self, time: Time) -> Task:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        raise NotImplementedError


__all__ = ['Scheduler']
