import abc
import logging
import os
from typing import Any

from pyobs.robotic.taskarchive import TaskArchive
from pyobs.utils.time import Time

from ...vfs import VirtualFileSystem
from ..task import Project, Task

log = logging.getLogger(__name__)


class FileSystemTaskArchive(TaskArchive, metaclass=abc.ABCMeta):
    """Task archive based on files."""

    def __init__(self, extension: str, path: str = "/robotic/tasks", **kwargs: Any):
        """Creates a new filesystem-based task archive.

        Args:
            extension: Extension of filesystem-based task-archive.
            path: Path to filesystem-based task-archive.
        """
        TaskArchive.__init__(self, **kwargs)
        self._path = path
        self._extension = extension

    @abc.abstractmethod
    async def _load_task_from_file(self, path: str, vfs: VirtualFileSystem) -> Task: ...

    async def last_changed(self) -> Time | None:
        """Returns time when last time any blocks changed."""
        return None

    async def get_projects(self) -> list[Project]:
        """Returns list of projects.

        Returns:
            List of projects.
        """
        raise NotImplementedError()

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        files = await self.vfs.find(self._path, f"*.{self._extension}")
        return [await self._load_task_from_file(os.path.join(self._path, f), self.vfs) for f in files]

    async def get_task(self, id: Any) -> Task:
        """Returns the task with the given ID.

        Returns:
            Task with given ID.
        """
        return await self._load_task_from_file(os.path.join(self._path, f"{id}.{self._extension}"), self.vfs)


class YamlTaskArchive(FileSystemTaskArchive):
    def __init__(self, **kwargs: Any):
        FileSystemTaskArchive.__init__(self, "yaml", **kwargs)

    async def _load_task_from_file(self, path: str, vfs: VirtualFileSystem) -> Task:
        config = await vfs.read_yaml(path)
        return self.pyobs_model_validate(Task, config)


__all__ = ["FileSystemTaskArchive", "YamlTaskArchive"]
