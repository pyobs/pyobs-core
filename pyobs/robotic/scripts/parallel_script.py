import asyncio
import logging

from typing import Any, Dict, Optional, List, Union

from pyobs.modules.robotic import ScriptRunner
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script


log = logging.getLogger(__name__)

class ParallelRunner(Script):
    """Script for running other scripts in parallel."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scripts: Union[List[Dict[str, Any]], Dict[str, Any]],
        **kwargs: Any,
    ):
        """Initialize a new ParallelRunner.

        Args:
            scripts: list or dict of scripts to run in parallel.
        """
        Script.__init__(self, **kwargs)

        if isinstance(scripts, Dict):
            scripts_ = []
            for key in scripts.keys():
                script = scripts[key]
                script['comm'] = self.comm
                scripts_.append(script)
            self.scripts = scripts_
        elif isinstance(scripts, List):
            for script in scripts:
                script['comm'] = self.comm
            self.scripts = scripts

    async def run(self,
                  task_runner: TaskRunner,
                  task_schedule: Optional[TaskSchedule] = None,
                  task_archive: Optional[TaskArchive] = None
                  ) -> None:
        tasks = [ScriptRunner(script)._run_thread() for script in self.scripts]
        await asyncio.gather(*tasks)


__all__ = ["ParallelRunner"]
