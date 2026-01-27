import copy
import logging
from typing import Dict, Optional, Any

from pyobs.utils.time import Time
from pyobs.robotic.taskarchive import TaskArchive
from .portal import Portal
from .task import LcoTask
from .. import Task

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
        self._portal = Portal(url, token)

        # store stuff
        self._url = url
        self._token = token
        instrument_type = [instrument_type] if isinstance(instrument_type, str) else instrument_type
        self._instrument_type = [it.lower() for it in instrument_type]

        # buffers in case of errors
        self._last_changed: Optional[Time] = None

        # task list
        self._tasks: Dict[str, LcoTask] = {}

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
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """

        # get data
        schedulable = await self._portal.schedulable_requests()

        # get proposal priorities
        proposals = await self._portal.proposals()
        tac_priorities = {p["id"]: p["tac_priority"] for p in proposals}

        # loop all request groups
        tasks: list[Task] = []
        for group in schedulable:
            # get base priority, which is tac_priority * ipp_value
            proposal = group["proposal"]
            if proposal not in tac_priorities:
                log.error('Could not find proposal "%s".', proposal)
                continue
            base_priority = group["ipp_value"] * tac_priorities[proposal]

            # loop all requests in group
            for req in group["requests"]:
                # still pending?
                if req["state"] != "PENDING":
                    continue

                # just take first config and ignore the rest
                cfg = req["configurations"][0]

                # get instrument and check, whether we schedule it
                instrument = cfg["instrument_type"]
                if instrument.lower() not in self._instrument_type:
                    continue

                # priority is base_priority times duration in minutes
                # priority = base_priority * duration.value / 60.
                priority = base_priority

                # copy group with just one request
                group_request = copy.deepcopy(group)
                del group_request["requests"]
                group_request["request"] = req
                group_request["priority"] = priority

                # create task
                tasks.append(LcoTask.from_lco_request(group_request))

        # return blocks
        return tasks


__all__ = ["LcoTaskArchive"]
