import logging
from typing import Any
from urllib.parse import urljoin
import requests

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from .. import Task

log = logging.getLogger(__name__)


class BackendTaskArchive(TaskArchive):
    """Task archive based on pyobs-robotic-backend."""

    def __init__(self, url: str, token: str, **kwargs: Any):
        """Creates a new task archive.

        Args:
            url: URL of pyobs-robotic-backend.
            token: Auth token.
        """
        TaskArchive.__init__(self, **kwargs)
        self._url = url
        self._token = token
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Token {self._token}"

    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed."""
        ...

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        req = requests.get(urljoin(self._url, "/api/tasks/"))
        return [Task.model_validate(task) for task in req.json()]

    async def get_task(self, id: Any) -> Task:
        """Returns the task with the given ID.

        Returns:
            Task with given ID.
        """
        req = requests.get(urljoin(self._url, f"/api/tasks/{id}/"))
        return Task.model_validate(req.json())


__all__ = ["BackendTaskArchive"]
