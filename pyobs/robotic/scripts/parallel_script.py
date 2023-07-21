import asyncio
import logging

from typing import Any, Dict, Optional

from pyobs.modules.robotic import ScriptRunner
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script


log = logging.getLogger(__name__)

class ParallelRunner(Script):
    """Script for running other scripts in parallel."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        config: Dict[str, Any],
        **kwargs: Any,
    ):
        """Initialize a new ParallelRunner.

        Args:
            script: Config for script to run.
        """
        # TODO: allow list of scripts as input
        Script.__init__(self, **kwargs)
        self._config = config
        scripts = []
        for key in config.keys():
            config_part = config[key]
            config_part['comm'] = self.comm
            scripts.append(config_part)
        self.scripts = scripts

    async def run(self,
                  task_runner: TaskRunner,
                  task_schedule: Optional[TaskSchedule] = None,
                  task_archive: Optional[TaskArchive] = None
                  ) -> None:
        tasks = [ScriptRunner(script)._run_thread() for script in self.scripts]
        await asyncio.gather(*tasks)

__all__ = ["ParallelRunner"]