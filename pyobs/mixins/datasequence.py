from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.interfaces import DataSequenceState, IDataSequence
from pyobs.modules import Module
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


class DataSequenceMixin(IDataSequence, metaclass=ABCMeta):
    """Implements IDataSequence.grab_sequence()/abort_sequence() on top of a host's grab_data().

    Shared by BaseCamera and BaseSpectrograph, whose grab_data() implementations differ only in
    what they grab. The host class must:
      - be a Module (comm is used to publish DataSequenceState)
      - implement grab_data(broadcast, **kwargs) -> str
      - implement _sequence_busy(), reporting whether it's busy outside of a running sequence
        (e.g. mid-exposure)
      - call _abort_data_sequence() from its own abort() implementation, so a hard abort also cuts
        short a sequence waiting out its inter-grab delay (there's no exception to catch in that
        case, unlike an abort during grab_data() itself, which grab_data() surfaces as a
        PyobsError that _run_sequence() below already ends the sequence on)
    """

    __module__ = "pyobs.mixins"

    def __init__(self, **kwargs: Any):
        # count_left > 0 means a sequence is currently running (also between individual grabs,
        # while the host's own status is briefly IDLE again)
        self._sequence_count_left = 0
        self._sequence_task: asyncio.Task[None] | None = None
        self._sequence_delay_abort = asyncio.Event()
        super().__init__(**kwargs)

    async def _datasequence_open(self) -> None:
        """Call from the host's open() to publish the initial idle sequence state."""
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")
        await self.comm.set_state(IDataSequence, DataSequenceState(count_total=0, count_left=0))

    @abstractmethod
    async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str: ...

    @abstractmethod
    def _sequence_busy(self) -> bool:
        """Whether the device is currently busy outside of a running sequence."""
        ...

    async def grab_sequence(self, count: int, broadcast: bool = True, delay: float = 0, **kwargs: Any) -> None:
        """Start a sequence of `count` grabs. Returns immediately; progress is available via
        the pushed DataSequenceState.

        Args:
            count: Number of grabs to take.
            broadcast: Broadcast existence of each grab.
            delay: Seconds to wait between the end of one grab and the start of the next.
                Does not apply after the last grab.

        Raises:
            InvalidArgumentError: If count or delay is out of range.
            DeviceBusyError: If the device is already busy (exposing or already running a
                sequence).
        """
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")

        if count < 1:
            raise exc.InvalidArgumentError("count must be >= 1.")
        if delay < 0:
            raise exc.InvalidArgumentError("delay must be >= 0.")

        if self._sequence_count_left > 0 or self._sequence_busy():
            raise exc.DeviceBusyError("Cannot start new sequence because device is not idle.")

        log.info("Starting sequence of %d grabs...", count)
        self._sequence_count_left = count
        await self.comm.set_state(IDataSequence, DataSequenceState(count_total=count, count_left=count))
        self._sequence_task = asyncio.create_task(self._run_sequence(count, broadcast, delay))

    async def _run_sequence(self, count_total: int, broadcast: bool, delay: float) -> None:
        """Runs a sequence of grab_data() calls, started by grab_sequence()."""
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")

        try:
            while self._sequence_count_left > 0:
                try:
                    await self.grab_data(broadcast=broadcast)
                except exc.PyobsError:
                    log.exception("Grab failed during sequence, aborting sequence.")
                    break
                self._sequence_count_left -= 1
                await self.comm.set_state(
                    IDataSequence, DataSequenceState(count_total=count_total, count_left=self._sequence_count_left)
                )

                # wait between grabs, unless this was the last one or the sequence was
                # aborted in the meantime -- either abort_sequence() or abort() cuts this short
                if self._sequence_count_left > 0 and delay > 0:
                    self._sequence_delay_abort.clear()
                    try:
                        await asyncio.wait_for(self._sequence_delay_abort.wait(), timeout=delay)
                    except TimeoutError:
                        pass
        finally:
            log.info("Finished sequence.")
            self._sequence_count_left = 0
            self._sequence_task = None
            await self.comm.set_state(IDataSequence, DataSequenceState(count_total=0, count_left=0))

    async def abort_sequence(self, **kwargs: Any) -> None:
        """Stop the sequence after the current grab. The grab currently in progress, if any,
        finishes normally; no further grabs in the sequence are started.
        """
        log.info("Aborting sequence after current grab...")
        self._abort_data_sequence()

    def _abort_data_sequence(self) -> None:
        """Clear sequence bookkeeping and cut short an in-progress inter-grab delay wait.

        Call this from the host's own abort() alongside its hardware-specific abort logic.
        """
        self._sequence_count_left = 0
        self._sequence_delay_abort.set()


__all__ = ["DataSequenceMixin"]
