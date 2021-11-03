from typing import Any

from .interface import Interface


class IScriptRunner(Interface):
    """The module can execute a script."""
    __module__ = 'pyobs.interfaces'

    def run_script(self, script: str, **kwargs: Any) -> None:
        """Run the given script.

        Args:
            script: Script to run.
        """
        raise NotImplementedError


__all__ = ['IScriptRunner']
