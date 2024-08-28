from __future__ import annotations
import logging
from typing import Any, List

from pyobs.interfaces import IMode
from pyobs.modules import Module

log = logging.getLogger(__name__)


class DummyMode(Module, IMode):
    """A dummy module for mode switching."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, **kwargs: Any):
        """Initialize a new dummy module."""
        Module.__init__(self, **kwargs)

        # modes
        self._mode_options = {
            "Size": ["XS", "S", "M", "L", "XL", "XXL"],
            "Speed": ["Slow", "Normal", "Fast"],
            "Movement": ["Rotation", "Linear"],
        }
        self._modes = {"Size": "M", "Speed": "Normal", "Movement": "Linear"}

    async def list_mode_groups(self, **kwargs: Any) -> List[str]:
        """List names of mode groups that can be set. The index is used as the `group` parameter in the individual
        methods.

        Returns:
            List of names of mode groups.
        """
        return list(self._mode_options.keys())

    def _group_name(self, group: int):
        return list(self._mode_options.keys())[group]

    async def list_modes(self, group: int = 0, **kwargs: Any) -> List[str]:
        """List available modes.

        Args:
            group: Group number

        Returns:
            List of available modes.
        """
        print(self._group_name(group))
        print(self._mode_options[self._group_name(group)])
        return self._mode_options[self._group_name(group)]

    async def set_mode(self, mode: str, group: int = 0, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.
            group: Group number

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode selector cannot be moved.
        """
        self._modes[self._group_name(group)] = mode

    async def get_mode(self, group: int = 0, **kwargs: Any) -> str:
        """Get currently set mode.

        Args:
            group: Group number

        Returns:
            Name of currently set mode.
        """
        return self._modes[self._group_name(group)]


__all__ = ["DummyMode"]
