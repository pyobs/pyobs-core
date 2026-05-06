from __future__ import annotations
from typing import Any, TYPE_CHECKING

from . import LcoTask
from .scripts import LcoScript
from .. import TaskRunner
from ..scripts import Script

if TYPE_CHECKING:
    from ..task import Task


class LcoTaskRunner(TaskRunner):

    def __init__(self, scripts: dict[str, Any], **kwargs: Any):
        """Creates a new LCO task runner.

        Args:
            scripts: External scripts
        """
        TaskRunner.__init__(self, **kwargs)
        self.scripts = scripts

    async def can_run(self, task: Task) -> bool:
        """Checks whether this task could run now.

        Args:
            task: Task to run

        Returns:
            True, if the task can run now.
        """
        if not isinstance(task, LcoTask):
            raise ValueError("Not an LCO task")
        task.script = self._get_config_script(task.config)
        return await TaskRunner.can_run(self, task)

    def _get_config_script(self, config: dict[str, Any]) -> Script:
        """Get config script for given configuration.

        Args:
            config: Config to create runner for.

        Returns:
            Script for running config

        Raises:
            ValueError: Could not create runner.
        """

        # what do we run?
        config_type = config["type"]
        if self.scripts is None or config_type not in self.scripts:
            raise ValueError('No script found for configuration type "%s".' % config_type)

        # create script handler
        script = Script.model_validate(self.scripts[config_type], by_alias=True)
        if isinstance(script, LcoScript):
            script.config = config
        return script


__all__ = ["LcoTaskRunner"]
