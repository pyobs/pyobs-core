import logging

from pyobs.interfaces import IScriptRunner
from pyobs.modules import Module
from pyobs.modules import timeout


log = logging.getLogger(__name__)


class ScriptRunner(Module, IScriptRunner):
    """Config provider."""
    __module__ = 'pyobs.modules.utils'

    def __init__(self, *args, **kwargs):
        """Initialize a new script runner."""
        Module.__init__(self, *args, **kwargs)

    @timeout(600)
    def run_script(self, script: str, *args, **kwargs):
        """Run the given script.

        Args:
            script: Script to run.

        Raises:
            Exception: If anything goes wrong while running the script.
        """

        # get all proxies
        proxies = {p: self.comm[p] for p in self.comm.clients}

        # execute it
        exec(script, proxies)


__all__ = ['ScriptRunner']
