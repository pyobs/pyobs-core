from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from pyobs.robotic.task import Project, Task
from pyobs.robotic.taskarchive import TaskArchive
from pyobs.utils.time import Time


class MemoryTaskArchive(TaskArchive):
    """In-memory task archive for testing and simple deployments."""

    def __init__(
        self,
        tasks: list[Task] | None = None,
        projects: list[Project] | None = None,
        on_tasks_changed: Callable[[], Coroutine[Any, Any, None]] | None = None,
        **kwargs: Any,
    ):
        TaskArchive.__init__(self, on_tasks_changed=on_tasks_changed, **kwargs)
        self._tasks: dict[str, Task] = {str(t.id): t for t in (tasks or [])}
        self._projects: list[Project] = projects or []
        self._last_changed: Time | None = None

    async def last_changed(self) -> Time | None:
        """Returns time when tasks last changed."""
        return self._last_changed

    async def get_projects(self) -> list[Project]:
        """Returns list of projects."""
        return list(self._projects)

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of all tasks."""
        return list(self._tasks.values())

    async def get_task(self, id: Any) -> Task | None:
        """Returns task with given ID, or None if not found."""
        return self._tasks.get(str(id))

    def add_task(self, task: Task) -> None:
        """Add or replace a task. Updates last_changed timestamp."""
        self._tasks[str(task.id)] = task
        self._last_changed = Time.now()

    def remove_task(self, task_id: Any) -> None:
        """Remove a task by ID."""
        self._tasks.pop(str(task_id), None)
        self._last_changed = Time.now()


__all__ = ["MemoryTaskArchive"]
