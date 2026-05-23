import asyncio
import logging
from typing import Any
from urllib.parse import urljoin
import aiohttp

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from ..task import Task, Project
from ...utils.http import http_request_with_retries

log = logging.getLogger(__name__)


class BackendTaskArchive(TaskArchive):
    """Task archive based on pyobs-robotic-backend."""

    def __init__(self, url: str, token: str, auto_update: bool = True, **kwargs: Any):
        """Creates a new task archive.

        Args:
            url: URL of pyobs-robotic-backend.
            token: Auth token.
        """
        TaskArchive.__init__(self, **kwargs)
        self._url = url
        self._token = token
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._last_update: Time | None = None
        self._projects: list[Project] = list()
        self._tasks: list[Task] = list()

        if auto_update:
            self.add_background_task(self._check_for_changes)

    async def open(self) -> None:
        """Opens the backend task archive."""
        await TaskArchive.open(self)
        self._aiohttp_session = aiohttp.ClientSession(headers={"Authorization": f"Token {self._token}"})

    @property
    def _session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None:
            raise ValueError("No session available.")
        return self._aiohttp_session

    async def _check_for_changes(self) -> None:
        """Update tasks in background."""
        while True:
            try:
                last_update = await self.last_update_time()
                if self._last_update is None or self._last_update < last_update:
                    self._projects = await self._get_projects()
                    self._tasks = await self._get_tasks()
                    log.info("Downloaded new tasks/projects.")
                    self._last_update = last_update
                    if self._on_tasks_changed is not None:
                        await self._on_tasks_changed()
            except Exception as e:
                log.error("Failed to update tasks from backend: %s", e)
            await asyncio.sleep(5)

    async def last_update_time(self) -> Time:
        """Fetches last schedule update time."""
        res = await http_request_with_retries(self._session, urljoin(self._url, "/api/last_task_update/"))
        return Time(res["last_task_update"])

    async def _get_projects(self) -> list[Project]:
        """Fetch projects from backend."""
        projects = await http_request_with_retries(self._session, urljoin(self._url, "/api/projects/"))
        return [self.pyobs_model_validate(Project, project) for project in projects]

    async def _get_tasks(self) -> list[Task]:
        """Fetch tasks from backend."""
        tasks = await http_request_with_retries(self._session, urljoin(self._url, "/api/tasks/"))
        return [self.pyobs_model_validate(Task, task) for task in tasks]

    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed."""
        return self._last_update

    async def get_projects(self) -> list[Project]:
        """Returns list of projects.

        Returns:
            List of projects.
        """
        return self._projects

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        return self._tasks

    async def get_task(self, id: Any) -> Task | None:
        """Returns the task with the given ID.

        Returns:
            Task with given ID.
        """
        for task in self._tasks:
            if task.id == id:
                return task
        else:
            return None


__all__ = ["BackendTaskArchive"]
