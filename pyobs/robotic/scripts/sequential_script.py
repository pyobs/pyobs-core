import logging
from typing import Any, Dict, Optional

from pyobs.modules.robotic import ScriptRunner
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)

class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        script: Dict[str, Any],
        **kwargs: Any,
    ):
        """Initialize a new SequentialRunner.

        Args:
            script: Config for script to run.
        """
        # TODO: allow list of scripts as input
        Script.__init__(self, **kwargs)
        self._script = script

    async def run(self,
                  task_runner: TaskRunner,
                  task_schedule: Optional[TaskSchedule] = None,
                  task_archive: Optional[TaskArchive] = None
                  ) -> None:
        script = self._script
        for key in script.keys():
            script_part = script[key]
            script_part['comm'] = self.comm
            await ScriptRunner(script_part)._run_thread()
        return

__all__ = ["SequentialRunner"]
