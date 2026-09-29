"""Tests for the BaseVideo frame buffer, see specs/design/basevideo-frame-source.md."""

from __future__ import annotations

import asyncio

import numpy as np
import pytest

from pyobs.modules.camera.videoframes import FrameBuffer, FrameRecord, FramesDroppedError, StartSource


def record(number: int, start: float | None = None) -> FrameRecord:
    return FrameRecord(
        number=number,
        data=np.zeros((2, 2)),
        arrival=1_700_000_000.0 + number,
        start=start,
        start_source=StartSource.DEVICE if start is not None else StartSource.UNKNOWN,
        exposure_time=None,
        generation=0,
    )


def test_size_must_be_positive() -> None:
    with pytest.raises(ValueError):
        FrameBuffer(0)


@pytest.mark.asyncio
async def test_latest_and_last_number() -> None:
    buffer = FrameBuffer(2)
    assert buffer.latest() is None
    assert buffer.last_number == -1

    for i in range(3):
        await buffer.add(record(i))

    assert buffer.latest().number == 2  # type: ignore[union-attr]
    assert buffer.last_number == 2


@pytest.mark.asyncio
async def test_wait_frame_finds_buffered_frame() -> None:
    buffer = FrameBuffer(4)
    await buffer.add(record(0))
    await buffer.add(record(1))

    frame = await asyncio.wait_for(buffer.wait_frame(lambda f: f.number >= 1), timeout=1)

    assert frame.number == 1


@pytest.mark.asyncio
async def test_wait_frame_waits_for_future_frame() -> None:
    buffer = FrameBuffer(4)
    await buffer.add(record(0))
    task = asyncio.create_task(buffer.wait_frame(lambda f: f.number == 2))

    await asyncio.sleep(0.01)
    await buffer.add(record(1))
    await asyncio.sleep(0.01)
    assert not task.done()
    await buffer.add(record(2))

    assert (await asyncio.wait_for(task, timeout=1)).number == 2


@pytest.mark.asyncio
async def test_wait_frame_checks_each_frame_once() -> None:
    buffer = FrameBuffer(4)
    calls: list[int] = []

    def predicate(frame: FrameRecord) -> bool:
        calls.append(frame.number)
        return frame.number == 2

    task = asyncio.create_task(buffer.wait_frame(predicate))
    for i in range(3):
        await asyncio.sleep(0.01)
        await buffer.add(record(i))
    await asyncio.wait_for(task, timeout=1)

    assert calls == [0, 1, 2]


@pytest.mark.asyncio
async def test_wait_newer_returns_newest_frame() -> None:
    buffer = FrameBuffer(4)
    for i in range(3):
        await buffer.add(record(i))

    assert (await asyncio.wait_for(buffer.wait_newer(0), timeout=1)).number == 2

    task = asyncio.create_task(buffer.wait_newer(2))
    await asyncio.sleep(0.01)
    assert not task.done()
    await buffer.add(record(3))
    assert (await asyncio.wait_for(task, timeout=1)).number == 3


@pytest.mark.asyncio
async def test_next_after_returns_consecutive_frames() -> None:
    buffer = FrameBuffer(4)
    await buffer.add(record(0))
    await buffer.add(record(1))

    assert (await buffer.next_after(0)).number == 1

    task = asyncio.create_task(buffer.next_after(1))
    await asyncio.sleep(0.01)
    await buffer.add(record(2))
    assert (await asyncio.wait_for(task, timeout=1)).number == 2


@pytest.mark.asyncio
async def test_next_after_raises_when_frame_was_dropped() -> None:
    buffer = FrameBuffer(2)
    for i in range(4):
        await buffer.add(record(i))

    with pytest.raises(FramesDroppedError):
        await buffer.next_after(0)


def test_date_obs_uses_start_or_arrival() -> None:
    assert record(0, start=1_700_000_000.0).date_obs == "2023-11-14T22:13:20.000000"
    assert record(0).date_obs == record(0).date_arrival
