import logging
from typing import Any, Dict

from pyobs.modules import Module
from pyobs.interfaces import IAutonomous
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class ScriptRunner(Module, IAutonomous):
    """Module for running a script."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        script: Dict[str, Any],
        **kwargs: Any,
    ):
        """Initialize a new script runner.
        Args:
            script: Config for script to run.
        """
        Module.__init__(self, **kwargs)

        # store
        self.script = script
        if 'comm' in script.keys():
            copy_comm = False
        else:
            copy_comm = True
        self._script = self.add_child_object(script, Script, configuration={}, copy_comm=copy_comm)
        # add thread func
        self.add_background_task(self._run_thread, False)

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        pass

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        pass

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return True

    async def _run_thread(self) -> None:
        """Run the script."""
        # run script
        await self._script.run(None)


__all__ = ["ScriptRunner"]