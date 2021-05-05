from .interface import *


class IScriptRunner(Interface):
    """The module can execute a script."""
    __module__ = 'pyobs.interfaces'

    def run_script(self, script: str, *args, **kwargs):
        """Run the given script.

        Args:
            script: Script to run.
        """
        raise NotImplementedError


__all__ = ['IScriptRunner']
