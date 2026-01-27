import abc
import logging
import os
from typing import Any

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from .. import Task
from ...vfs import VirtualFileSystem

log = logging.getLogger(__name__)


class FileSystemTaskArchive(TaskArchive, metaclass=abc.ABCMeta):
    """Task archive based on files."""

    def __init__(self, path: str, extension: str, **kwargs: Any):
        """Creates a new filesystem-based task archive.

        Args:
            path: Path to filesystem-based task-archive.
            extension: Extension of filesystem-based task-archive.
        """
        TaskArchive.__init__(self, **kwargs)
        self._path = path
        self._extension = extension

    @classmethod
    @abc.abstractmethod
    async def from_file(cls, path: str, vfs: VirtualFileSystem) -> Task: ...

    async def last_changed(self) -> Time | None:
        """Returns time when last time any blocks changed."""
        return None

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        files = await self.vfs.find(self._path, f"*.{self._extension}")
        return [await self.from_file(os.path.join(self._path, f), self.vfs) for f in files]


class YamlTaskArchive(FileSystemTaskArchive):
    def __init__(self, path: str, **kwargs: Any):
        FileSystemTaskArchive.__init__(self, path, "yaml", **kwargs)

    @classmethod
    async def from_file(cls, path: str, vfs: VirtualFileSystem) -> Task:
        config = await vfs.read_yaml(path)
        return Task.from_dict(config)


__all__ = ["FileSystemTaskArchive", "YamlTaskArchive"]
