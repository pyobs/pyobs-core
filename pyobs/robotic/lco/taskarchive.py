import asyncio
import logging
import astropy.units as u
from typing import Any
from typing_extensions import override
from astropy.time import TimeDelta

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from ._portal import Portal
from .task import LcoTask
from ..task import Project

log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        token: str,
        instrument_type: str | list[str],
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            token: Authorization token for portal
            instrument_type: Type of instrument to use.
            scripts: External scripts
        """
        TaskArchive.__init__(self, **kwargs)

        # portal
        self._portal = self.add_child_object(Portal(url, token, "", "", ""))

        # store stuff
        instrument_type = [instrument_type] if isinstance(instrument_type, str) else instrument_type
        self._instrument_type = [it.lower() for it in instrument_type]

        # buffers in case of errors
        self._last_changed: Time | None = None

        # task list
        self._projects: list[Project] = list()
        self._tasks: list[LcoTask] = list()

        # update task
        self.add_background_task(self._check_for_changes)

    async def _check_for_changes(self) -> None:
        # time of last change in blocks
        last_change = None

        # run forever
        while True:
            try:
                # got new time of last change?
                t = await self._portal.last_changed()
                more_1day = (Time.now() - t) > TimeDelta(1 * u.day)
                if last_change is None or last_change < t and not more_1day:
                    last_change = t
                    self._tasks, self._projects = await self._get_tasks_and_projects()
                    if self._on_tasks_changed is not None:
                        asyncio.create_task(self._on_tasks_changed())
            except Exception as e:
                log.error("Failed to update tasks from backend: %s", e)

            # sleep a little
            await asyncio.sleep(5)

    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed."""
        return self._last_changed

    async def get_projects(self) -> list[Project]:
        """Returns list of projects from the LCO portal."""
        return self._projects

    @override
    async def get_schedulable_tasks(self) -> list[LcoTask]:  # type: ignore[override]
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        return self._tasks

    @override
    async def get_task(self, id: Any) -> LcoTask | None:
        """Returns the task with the given ID."""
        for task in self._tasks:
            if task.id == id:
                return task
        return None

    async def _get_tasks_and_projects(self) -> tuple[list[LcoTask], list[Project]]:
        """Returns a list of schedulable tasks and projects

        Returns:
            List of schedulable tasks and projects
        """

        # get data
        schedulable_requests = await self._portal.schedulable_requests()

        # get proposal priorities
        proposals = await self._portal.proposals()
        tac_priorities = {p["id"]: p["tac_priority"] for p in proposals}

        # to LcoTasks
        all_tasks: list[LcoTask] = []
        for schedulable_request in schedulable_requests:
            tasks = LcoTask.from_schedulable_request(schedulable_request, {})
            for task in tasks:
                task.priority = schedulable_request.ipp_value * tac_priorities[schedulable_request.proposal]
                if task.request.state != "PENDING":
                    continue
                if task.request.configurations[0].instrument_type.lower() not in self._instrument_type:
                    continue
                all_tasks.append(task)

        # return tasks
        return all_tasks, [Project(code=p["id"], name=p["id"], priority=p.get("tac_priority", 1.0)) for p in proposals]


__all__ = ["LcoTaskArchive"]
