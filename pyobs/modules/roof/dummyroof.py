import asyncio
import logging
from typing import Any, Optional

from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.interfaces import IRoof
from pyobs.modules import timeout
from pyobs.modules.roof import BaseRoof
from pyobs.utils.enums import MotionStatus
from pyobs.utils.threads import LockWithAbort

log = logging.getLogger(__name__)


class DummyRoof(BaseRoof, IRoof):
    """A dummy camera for testing."""

    __module__ = "pyobs.modules.roof"

    _ROOF_CLOSED_PERCENTAGE = 0
    _ROOF_OPEN_PERCENTAGE = 100

    def __init__(self, **kwargs: Any):
        """Creates a new dummy root."""
        BaseRoof.__init__(self, **kwargs)

        # dummy state
        self._open_percentage: int = self._ROOF_CLOSED_PERCENTAGE

        self._lock_motion = asyncio.Lock()
        self._abort_motion = asyncio.Event()

    async def open(self) -> None:
        """Open module."""
        await BaseRoof.open(self)

        await self.comm.register_event(RoofOpenedEvent)
        await self.comm.register_event(RoofClosingEvent)

    @timeout(15)
    async def init(self, **kwargs: Any) -> None:
        """Open the roof.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        if self._is_open():
            return

        async with LockWithAbort(self._lock_motion, self._abort_motion):
            await self._change_motion_status(MotionStatus.INITIALIZING)

            await self._move_roof(self._ROOF_OPEN_PERCENTAGE)

            await self._change_motion_status(MotionStatus.IDLE)
            await self.comm.send_event(RoofOpenedEvent())

    def _is_open(self) -> bool:
        return self._open_percentage == self._ROOF_OPEN_PERCENTAGE

    @timeout(15)
    async def park(self, **kwargs: Any) -> None:
        """Close the roof.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        if self._is_closed():
            return

        async with LockWithAbort(self._lock_motion, self._abort_motion):
            await self._change_motion_status(MotionStatus.PARKING)
            await self.comm.send_event(RoofClosingEvent())

            await self._move_roof(self._ROOF_CLOSED_PERCENTAGE)

            await self._change_motion_status(MotionStatus.PARKED)

    def _is_closed(self) -> bool:
        return self._open_percentage == self._ROOF_CLOSED_PERCENTAGE

    async def _move_roof(self, target_pos: int) -> None:
        step = 1 if target_pos > self._open_percentage else -1

        while self._open_percentage != target_pos:
            if self._abort_motion.is_set():
                await self._change_motion_status(MotionStatus.IDLE)
                return

            self._open_percentage += step
            await asyncio.sleep(0.1)

    def get_percent_open(self) -> float:
        """Get the percentage the roof is open."""
        return self._open_percentage

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        await self._change_motion_status(MotionStatus.ABORTING)

        async with LockWithAbort(self._lock_motion, self._abort_motion):
            await self._change_motion_status(MotionStatus.IDLE)


__all__ = ["DummyRoof"]
