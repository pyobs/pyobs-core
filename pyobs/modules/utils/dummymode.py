from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.events import ModeChangedEvent
from pyobs.interfaces import IMode, IMotion, ModeCapabilities, ModeState
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
        if isinstance(self, Module) and self._comm:
            await self.comm.register_event(ModeChangedEvent)

        # publish capabilities and initial state
        await self.comm.set_capabilities(IMode, ModeCapabilities(modes=self._mode_options))
        await self.comm.set_state(IMode, ModeState(modes=dict(self._modes)))

    async def set_mode(self, mode: str, group: str = "", **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.
            group: Name of the group to set the mode for.

        Raises:
            ValueError: If an invalid mode or group was given.
            MoveError: If mode selector cannot be moved.
        """
        if not group:
            group = next(iter(self._mode_options.keys()))
        if group not in self._mode_options:
            raise ValueError(f"Invalid group: {group}")
        await self._change_motion_status(MotionStatus.SLEWING)
        try:
            await asyncio.wait_for(asyncio.shield(self._closing.wait()), timeout=3.0)
            # closing was set — abort
            return
        except TimeoutError:
            pass  # normal case: 3 seconds elapsed
        self._modes[group] = mode
        await self._change_motion_status(MotionStatus.POSITIONED)
        await self.comm.send_event(ModeChangedEvent(group, mode))
        await self.comm.set_state(IMode, ModeState(modes=dict(self._modes)))

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        pass


__all__ = ["DummyMode"]
