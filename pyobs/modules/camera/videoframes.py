from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from numpy.typing import NDArray


class StartSource(StrEnum):
    """Where a frame's exposure start time came from."""

    DEVICE = "device"
    """Supplied by the driver, e.g. a hardware timestamp."""

    ESTIMATED = "estimated"
    """Estimated as arrival time minus exposure time minus readout time."""

    UNKNOWN = "unknown"
    """Neither a start time nor an exposure time was available."""


@dataclass(frozen=True)
class Frame:
    """A single frame, as yielded by a driver's BaseVideo.frames() iterator.

    The driver hands ownership of ``data`` to BaseVideo: it must not reuse or modify the array
    afterwards. Drivers that recycle SDK buffers copy before yielding.
    """

    data: NDArray[Any]
    """Image data."""

    start: float | None = None
    """Exposure start as UTC unix time, or None if the driver can't tell."""

    exposure_time: float | None = None
    """Exposure time in seconds, as actually applied by the camera, or None if unknown."""

    generation: int | None = None
    """Settings generation in effect when the exposure started, or None for BaseVideo's current one."""


@dataclass(frozen=True)
class FrameRecord:
    """A frame as stored in the FrameBuffer, with the bookkeeping BaseVideo adds on arrival."""

    number: int
    """Frame number, increasing by one per frame since module start."""

    data: NDArray[Any]
    """Image data, already flipped if the module is configured to flip."""

    arrival: float
    """UTC unix time the frame reached BaseVideo."""

    start: float | None
    """Exposure start as UTC unix time, or None if unknown (see start_source)."""

    start_source: StartSource
    """Where the start time came from."""

    exposure_time: float | None
    """Exposure time in seconds, or None if unknown."""

    generation: int
    """Settings generation in effect when the exposure started."""

    @property
    def date_obs(self) -> str:
        """Exposure start, or arrival time if the start is unknown, as ISO string for DATE-OBS."""
        return _isot(self.start if self.start is not None else self.arrival)

    @property
    def date_arrival(self) -> str:
        """Arrival time as ISO string."""
        return _isot(self.arrival)


def _isot(t: float) -> str:
    return datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")


class FramesDroppedError(Exception):
    """A consumer asked for a frame that has already been pushed out of the buffer."""


class FrameBuffer:
    """Ring buffer of the most recent frames, shared by all consumers of a BaseVideo module.

    The frame loop only appends; everything else (grabbing, live view, raw stream) waits on the
    buffer. Consumers never block the producer: a consumer that falls behind by more than the
    buffer size either gets the newest frame (latest-wins consumers) or a FramesDroppedError
    (consumers that need consecutive frames).
    """

    def __init__(self, size: int = 4):
        """Creates a new frame buffer.

        Args:
            size: Number of frames to keep.
        """
        if size < 1:
            raise ValueError("Frame buffer size must be at least 1.")
        self._frames: deque[FrameRecord] = deque(maxlen=size)
        self._cond = asyncio.Condition()

    @property
    def size(self) -> int:
        """Maximum number of frames kept."""
        return self._frames.maxlen or 0

    def latest(self) -> FrameRecord | None:
        """Returns the newest frame, or None if there is none yet."""
        return self._frames[-1] if self._frames else None

    @property
    def last_number(self) -> int:
        """Number of the newest frame, or -1 if there is none yet."""
        return self._frames[-1].number if self._frames else -1

    async def add(self, record: FrameRecord) -> None:
        """Appends a frame and wakes up all waiting consumers.

        Args:
            record: New frame.
        """
        async with self._cond:
            self._frames.append(record)
            self._cond.notify_all()

    async def wait_frame(self, predicate: Callable[[FrameRecord], bool]) -> FrameRecord:
        """Waits for the first frame, already buffered or future, that matches the predicate.

        Args:
            predicate: Function that returns True for a matching frame.

        Returns:
            The first matching frame.
        """
        async with self._cond:
            checked = -1
            while True:
                for frame in self._frames:
                    if frame.number > checked:
                        checked = frame.number
                        if predicate(frame):
                            return frame
                await self._cond.wait()

    async def wait_newer(self, number: int) -> FrameRecord:
        """Waits for a frame newer than the given number and returns the newest one.

        Latest-wins: if several frames arrived in the meantime, only the newest is returned.

        Args:
            number: Number of the last frame the consumer has seen, -1 for none.

        Returns:
            Newest frame.
        """
        async with self._cond:
            await self._cond.wait_for(lambda: self.last_number > number)
            return self._frames[-1]

    async def next_after(self, number: int) -> FrameRecord:
        """Waits for the frame directly following the given one.

        Args:
            number: Number of the last frame the consumer has seen.

        Returns:
            Frame with number ``number + 1``.

        Raises:
            FramesDroppedError: If that frame has already been pushed out of the buffer.
        """
        wanted = number + 1
        async with self._cond:
            while True:
                if self._frames and self._frames[0].number > wanted:
                    raise FramesDroppedError(f"Frame {wanted} is no longer in the buffer.")
                for frame in self._frames:
                    if frame.number == wanted:
                        return frame
                await self._cond.wait()


__all__ = ["Frame", "FrameRecord", "FrameBuffer", "FramesDroppedError", "StartSource"]
