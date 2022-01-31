import logging
from typing import Dict, Optional, Any

from pyobs.robotic.task import Task
from pyobs.robotic.taskrunner import TaskRunner


log = logging.getLogger(__name__)


class LcoTaskRunner(TaskRunner):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        scripts: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            period: Period to schedule in hours
            scripts: External scripts
        """
        TaskRunner.__init__(self, **kwargs)

        # store stuff
        self._scripts = scripts

    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """

        # run task
        await task.run()

        # force update tasks
        await self._update_now(force=True)

        # finish
        return True


__all__ = ["LcoTaskRunner"]
