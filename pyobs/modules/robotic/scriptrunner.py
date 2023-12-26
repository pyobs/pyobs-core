import logging
from typing import Any, Dict

from pyobs.modules import Module, timeout
from pyobs.interfaces import IRunnable
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


async def calc_run_timeout(obj: "ScriptRunner", *args: Any, **kwargs: Any) -> float:
    """Calculates timeout for run()."""
    return obj.timeout


class ScriptRunner(Module, IRunnable):
    """Module for running a script."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        script: Dict[str, Any],
        run_once: bool = False,
        timeout: int = 10,
        **kwargs: Any,
    ):
        """Initialize a new script runner.

        Args:
            script: Config for script to run.
        """
        Module.__init__(self, **kwargs)

        # store
        self.script = script
        self._script = self.add_child_object(script, Script)
        self.timeout = timeout

        # add thread func
        if run_once:
            self.add_background_task(self._run_thread, False)

    @timeout(calc_run_timeout)
    async def run(self, **kwargs: Any) -> None:
        """Run script."""
        script = self.get_object(self.script, Script)
        await script.run(None)

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        pass

    async def _run_thread(self) -> None:
        """Run the script."""
        await self.run()


__all__ = ["ScriptRunner"]
