import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

import aiohttp

from pyobs.robotic.storage.taskarchive import TaskArchive
from pyobs.robotic.task import Project, Task
from pyobs.utils.http import LogThrottle, http_request_paginated, http_request_with_retries
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PortalTaskArchive(TaskArchive):
    """Task archive based on pyobs-portal."""

    def __init__(self, url: str, token: str, auto_update: bool = True, **kwargs: Any):
        """Creates a new task archive.

        Args:
            url: URL of pyobs-portal.
            token: Auth token.
        """
        TaskArchive.__init__(self, **kwargs)
        self._url = url
        self._token = token
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._last_update: Time | None = None
        self._last_marker: Time | None = None
        self._projects: list[Project] = list()
        self._tasks: list[Task] = list()
        # First failure logs immediately at ERROR (someone should know right away); repeats
        # during the same outage are throttled to at most one ERROR per minute.
        self._poll_error_throttle = LogThrottle(quiet_for=0.0, interval=60.0)

        if auto_update:
            self.add_background_task(self._check_for_changes)

    async def open(self) -> None:
        """Opens the portal task archive."""
        self._aiohttp_session = aiohttp.ClientSession(headers={"Authorization": f"Token {self._token}"})
        await TaskArchive.open(self)

    async def close(self) -> None:
        """Closes the portal task archive."""
        await TaskArchive.close(self)
        if self._aiohttp_session is not None:
            await self._aiohttp_session.close()
            self._aiohttp_session = None

    @property
    def _session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None:
            raise ValueError("No session available.")
        return self._aiohttp_session

    async def _check_for_changes(self) -> None:
        """Update tasks in background, gated on the portal's update marker."""
        while True:
            try:
                await self._poll()
                self._poll_error_throttle.clear("poll")
            except Exception as e:
                if self._poll_error_throttle.should_escalate("poll"):
                    log.error("Failed to update tasks from portal: %s", e)
                else:
                    log.debug("Failed to update tasks from portal: %s", e)
            await asyncio.sleep(5)

    async def _poll(self) -> None:
        """Re-download tasks/projects when the portal's ``last_task_update`` marker moved.

        The marker is a DB-derived ``Max(updated_at)`` (pyobs-portal#84), truthful across
        gunicorn workers, so it is a safe refresh gate. Without it the archive re-downloaded (and
        re-compared) on every poll, and the content comparison misfired whenever runtime code
        mutated a serialized task field (e.g. ``DynamicTarget.resolve()`` overwriting ``name``),
        livelocking the scheduler. The content comparison in :meth:`_update` still decides whether
        to fire ``on_tasks_changed``.
        """
        last_update = await self.last_update_time()
        if self._last_marker is None or last_update > self._last_marker:
            await self._update()
            self._last_marker = last_update

    async def _update(self) -> None:
        """Fetch tasks/projects from the portal and apply them if anything changed.

        Called by :meth:`_poll` after the portal marker moved (or on the first poll); applies the
        download only when the content actually differs from the cached copy. The comparison uses
        ``model_dump()`` rather than pydantic ``==``, which also compares runtime attributes (e.g.
        ``Task._cant_run_reason`` set by ``can_run()``) and would flag unchanged tasks as changed
        on every poll; it is keyed by ID so that a stable reordering of the same items (e.g. an
        unordered portal queryset) is not mistaken for a change.
        """
        projects = await self._get_projects()
        tasks = await self._get_tasks()
        if {p.code: p.model_dump() for p in projects} != {p.code: p.model_dump() for p in self._projects} or {
            t.id: t.model_dump() for t in tasks
        } != {t.id: t.model_dump() for t in self._tasks}:
            self._projects = projects
            self._tasks = tasks
            self._last_update = Time.now()
            log.info("Downloaded new tasks/projects.")
            if self._on_tasks_changed is not None:
                await self._on_tasks_changed()

    async def last_update_time(self) -> Time:
        """Fetches last schedule update time."""
        res = await http_request_with_retries(self._session, urljoin(self._url, "/api/last_task_update/"))
        return Time(res["last_task_update"])

    async def _get_projects(self) -> list[Project]:
        """Fetch projects from portal."""
        projects = await http_request_paginated(self._session, urljoin(self._url, "/api/projects/"), strict=True)
        return [self.pyobs_model_validate(Project, project) for project in projects]

    async def _get_tasks(self) -> list[Task]:
        """Fetch tasks from portal."""
        tasks = await http_request_paginated(self._session, urljoin(self._url, "/api/tasks/"), strict=True)
        return [self.pyobs_model_validate(Task, task) for task in tasks]

    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed (as observed by this archive).

        This is the local time at which the last content change was detected by the polling loop,
        not the portal's marker timestamp -- the marker is per-process and unreliable.
        """
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


__all__ = ["PortalTaskArchive"]
