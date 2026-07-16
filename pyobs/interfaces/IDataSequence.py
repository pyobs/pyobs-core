from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IAbortable import IAbortable


@dataclass
class DataSequenceState:
    count_total: int  # 0 when idle / no sequence running
    count_left: int
    time: Time = field(default_factory=Time.now)


class IDataSequence(IAbortable, metaclass=ABCMeta):
    """The module can grab a counted sequence of data (images, spectra, ...)."""

    __module__ = "pyobs.interfaces"

    state = DataSequenceState

    @abstractmethod
    async def grab_sequence(
        self, count: int, broadcast: bool = True, delay: Annotated[float, Unit.SECONDS] = 0, **kwargs: Any
    ) -> None:
        """Start a sequence of `count` grabs. Returns immediately; progress is available via
        the pushed DataSequenceState.

        Args:
            count: Number of grabs to take.
            broadcast: Broadcast existence of each grab.
            delay: Seconds to wait between the end of one grab and the start of the next.
                Does not apply after the last grab. Skipped early if the sequence is aborted
                during the wait.

        Raises:
            GrabImageError: If the device is already busy (exposing or already running a
                sequence).
        """
        ...

    @abstractmethod
    async def abort_sequence(self, **kwargs: Any) -> None:
        """Stop the sequence after the current grab. The grab currently in progress, if any,
        finishes normally; no further grabs in the sequence are started.

        This is the graceful counterpart to IAbortable.abort(), which remains the hard-stop
        path: it cancels the running grab immediately *and* the remaining sequence count.
        """
        ...


__all__ = ["IDataSequence", "DataSequenceState"]
