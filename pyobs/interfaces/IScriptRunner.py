from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IScriptRunner(Interface, metaclass=ABCMeta):
    """The module can execute a script."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def run_script(self, script: str, **kwargs: Any) -> None:
        """Run the given script.

        Args:
            script: Script to run.
        """
        ...


__all__ = ['IScriptRunner']
