import asyncio
import logging
import astropy.units as u
from typing import Dict, Optional, Any
from astropy.time import TimeDelta

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from ._portal import Portal
from .task import LcoTask
from .. import Task
from ..scripts import Script

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
        self._portal = Portal(url, token, "", "", "")

        # store stuff
        instrument_type = [instrument_type] if isinstance(instrument_type, str) else instrument_type
        self._instrument_type = [it.lower() for it in instrument_type]

        # buffers in case of errors
        self._last_changed: Optional[Time] = None

        # task list
        self._tasks: Dict[str, LcoTask] = {}

        # update task
        self.add_background_task(self._update_worker)

    async def _update_worker(self) -> None:
        # time of last change in blocks
        last_change = None

        # run forever
        while True:
            # got new time of last change?
            t = await self._portal.last_changed()
            more_1day = (Time.now() - t) > TimeDelta(1 * u.day)
            if last_change is None or last_change < t and not more_1day:
                try:
                    last_change = t
                    if self._on_tasks_changed is not None:
                        asyncio.create_task(self._on_tasks_changed())
                except asyncio.CancelledError:
                    return
                except:
                    log.exception("Something went wrong when updating schedule.")

            # sleep a little
            await asyncio.sleep(5)

    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""

        # try to update time
        try:
            self._last_changed = await self._portal.last_changed()
        except:
            log.error("Could not get last changed time")

        # even in case of errors, return last time
        return self._last_changed

    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns a list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """

        # get data
        schedulable_requests = await self._portal.schedulable_requests()

        # get proposal priorities
        proposals = await self._portal.proposals()
        tac_priorities = {p["id"]: p["tac_priority"] for p in proposals}

        # to LcoTasks
        all_tasks: list[Task] = []
        for schedulable_request in schedulable_requests:
            tasks = LcoTask.from_schedulable_request(schedulable_request, Script())
            for task in tasks:
                task.priority = schedulable_request.ipp_value * tac_priorities[schedulable_request.proposal]
                if task.request.state == "PENDING":
                    continue
                if task.request.configurations[0].instrument_type.lower() not in self._instrument_type:
                    continue
                all_tasks.append(task)

        # return tasks
        return all_tasks


__all__ = ["LcoTaskArchive"]
