from __future__ import annotations
from typing import Any, TYPE_CHECKING

from . import LcoTask
from ._portal import LcoRequest
from .. import TaskRunner

if TYPE_CHECKING:
    from ..task import Task


class LcoTaskRunner(TaskRunner):

    scripts: dict[str, dict[str, Any]]

    def __init__(self, scripts: dict[str, Any], **kwargs: Any):
        """Creates a new LCO task runner.

        Args:
            scripts: External scripts
        """
        TaskRunner.__init__(self, **kwargs)
        self.scripts = scripts

    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """
        if not isinstance(task, LcoTask):
            raise ValueError("Not an LCO task")
        task.script = self._get_config_script(task.request)
        return await TaskRunner.run_task(self, task)

    async def can_run(self, task: Task) -> bool:
        """Checks whether this task could run now.

        Args:
            task: Task to run

        Returns:
            True, if the task can run now.
        """
        if not isinstance(task, LcoTask):
            raise ValueError("Not an LCO task")
        task.script = self._get_config_script(task.request)
        return await TaskRunner.can_run(self, task)

    def _get_config_script(self, request: LcoRequest) -> dict[str, Any]:
        """Get config script for given configuration.

        Args:
            request: LCO request.

        Returns:
            Script for running config

        Raises:
            ValueError: Could not create runner.
        """

        # what do we run?
        config_type = request.configurations[0].type
        if self.scripts is None or config_type not in self.scripts:
            raise ValueError('No script found for configuration type "%s".' % config_type)
        return self.scripts[config_type]


__all__ = ["LcoTaskRunner"]
