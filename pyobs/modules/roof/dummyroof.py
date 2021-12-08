import asyncio
import logging
import threading
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
    __module__ = 'pyobs.modules.roof'

    def __init__(self, **kwargs: Any):
        """Creates a new dummy root."""
        BaseRoof.__init__(self, **kwargs)

        # dummy state
        self.open_percentage = 0

        # allow to abort motion
        self._lock_motion = threading.Lock()
        self._abort_motion = threading.Event()

        # register event
        await self.comm.register_event(RoofOpenedEvent)
        await self.comm.register_event(RoofClosingEvent)

    @timeout(15)
    async def open_roof(self, **kwargs: Any) -> None:
        """Open the roof.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        # already open?
        if self.open_percentage != 100:
            # acquire lock
            with LockWithAbort(self._lock_motion, self._abort_motion):
                # change status
                await self._change_motion_status(MotionStatus.INITIALIZING)

                # open roof
                while self.open_percentage < 100:
                    # open more
                    self.open_percentage += 1

                    # abort?
                    if self._abort_motion.is_set():
                        await self._change_motion_status(MotionStatus.IDLE)
                        return

                    # wait a little
                    await asyncio.sleep(0.1)

                # open fully
                self.open_percentage = 100

                # change status
                await self._change_motion_status(MotionStatus.IDLE)

                # send event
                self.comm.send_event(RoofOpenedEvent())

    @timeout(15)
    async def close_roof(self, **kwargs: Any) -> None:
        """Close the roof.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        # already closed?
        if self.open_percentage != 0:
            # acquire lock
            with LockWithAbort(self._lock_motion, self._abort_motion):
                # change status
                await self._change_motion_status(MotionStatus.PARKING)

                # send event
                self.comm.send_event(RoofClosingEvent())

                # close roof
                while self.open_percentage > 0:
                    # close more
                    self.open_percentage -= 1

                    # abort?
                    if self._abort_motion.is_set():
                        await self._change_motion_status(MotionStatus.IDLE)
                        return

                    # wait a little
                    await asyncio.sleep(0.1)

                # change status
                await self._change_motion_status(MotionStatus.PARKED)

    def get_percent_open(self) -> float:
        """Get the percentage the roof is open."""
        return self.open_percentage

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.

        Raises:
            AcquireLockFailed: If current motion could not be aborted.
        """

        # change status
        await self._change_motion_status(MotionStatus.ABORTING)

        # abort
        # acquire lock
        with LockWithAbort(self._lock_motion, self._abort_motion):
            # change status
            await self._change_motion_status(MotionStatus.IDLE)


__all__ = ['DummyRoof']
