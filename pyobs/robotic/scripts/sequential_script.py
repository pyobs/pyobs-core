import logging
from typing import Any, Dict, Optional, Union, List

from pyobs.modules.robotic import ScriptRunner
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)

class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scripts: Union[List[Dict[str, Any]], Dict[str, Any]],
        **kwargs: Any,
    ):
        """Initialize a new SequentialRunner.

        Args:
            script: list or dict of scripts to run in a sequence.
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
        for script in self.scripts:
            await ScriptRunner(script)._run_thread()
        return

__all__ = ["SequentialRunner"]
