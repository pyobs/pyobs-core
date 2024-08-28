from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional

from pyobs.events import ModeChangedEvent
from pyobs.interfaces import IMode, IMotion
from pyobs.mixins import MotionStatusMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class DummyMode(MotionStatusMixin, Module, IMode, IMotion):
    """A dummy module for mode switching."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, **kwargs: Any):
        """Initialize a new dummy module."""
        Module.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)

        # modes
        self._mode_options = {
            "Size": ["XS", "S", "M", "L", "XL", "XXL"],
            "Speed": ["Slow", "Normal", "Fast"],
            "Movement": ["Rotation", "Linear"],
        }
        self._modes = {"Size": "M", "Speed": "Normal", "Movement": "Linear"}

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # open mixins
        await MotionStatusMixin.open(self)
        await self._change_motion_status(MotionStatus.POSITIONED)

        # subscribe to events
        if isinstance(self, Module) and self.comm:
            await self.comm.register_event(ModeChangedEvent)

    async def list_mode_groups(self, **kwargs: Any) -> List[str]:
        """List names of mode groups that can be set. The index is used as the `group` parameter in the individual
        methods.

        Returns:
            List of names of mode groups.
        """
        return list(self._mode_options.keys())

    def _group_name(self, group: int):
        try:
            return list(self._mode_options.keys())[group]
        except IndexError:
            return ""

    async def list_modes(self, group: int = 0, **kwargs: Any) -> List[str]:
        """List available modes.

        Args:
            group: Group number

        Returns:
            List of available modes.
        """
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
        await self._change_motion_status(MotionStatus.SLEWING)
        await asyncio.sleep(3)
        self._modes[self._group_name(group)] = mode
        await self._change_motion_status(MotionStatus.POSITIONED)
        await self.comm.send_event(ModeChangedEvent(list(self._mode_options.keys())[group], mode))

    async def get_mode(self, group: int = 0, **kwargs: Any) -> str:
        """Get currently set mode.

        Args:
            group: Group number

        Returns:
            Name of currently set mode.
        """
        return self._modes[self._group_name(group)]

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        pass

    async def is_ready(self, **kwargs: Any) -> bool:
        return True


__all__ = ["DummyMode"]
