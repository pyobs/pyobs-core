from .interface import *


class IScriptRunner(Interface):
    """Interface for running a script."""

    def run_script(self, script: str, *args, **kwargs):
        """Run the given script.

        Args:
            script: Script to run.
        """
        raise NotImplementedError


__all__ = ['IScriptRunner']
