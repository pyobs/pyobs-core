"""Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence implementation.

Covers #548. grab_data() itself is mocked out in most tests here -- these tests are about the
sequencing logic (grab_sequence/_run_sequence/abort_sequence/abort interplay and the pushed
DataSequenceState), not about exposure/VFS/FITS-header mechanics, which are exercised elsewhere.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from pyobs.interfaces import IDataSequence
from pyobs.modules.camera import DummyCamera
from pyobs.utils import exceptions as exc


def make_camera() -> DummyCamera:
    camera = DummyCamera(readout_time=0)
    camera.comm.set_state = AsyncMock()
    return camera


@pytest.mark.asyncio
async def test_grab_sequence_returns_immediately() -> None:
    """grab_sequence() must not block for the whole sequence -- see design doc: a blocking
    call here would be exactly the shape of RPC that caused #664/#666."""
    camera = make_camera()
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        await gate.wait()
        return "f.fits"

    camera.grab_data = fake_grab_data

    await asyncio.wait_for(camera.grab_sequence(3), timeout=1.0)

    # sequence is running but hasn't finished -- grab_sequence() returned anyway
    assert camera._sequence_count_left == 3
    gate.set()
    assert camera._sequence_task is not None
    await camera._sequence_task


@pytest.mark.asyncio
async def test_grab_sequence_runs_count_times() -> None:
    camera = make_camera()
    calls = 0

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(3)
    assert camera._sequence_task is not None
    await camera._sequence_task

    assert calls == 3
    assert camera._sequence_count_left == 0
    assert camera._sequence_task is None


@pytest.mark.asyncio
async def test_grab_sequence_pushes_progressing_state() -> None:
    camera = make_camera()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(2)
    assert camera._sequence_task is not None
    await camera._sequence_task

    pushed = [
        (call.args[1].count_total, call.args[1].count_left)
        for call in camera.comm.set_state.call_args_list
        if call.args[0] is IDataSequence
    ]
    assert pushed == [
        (2, 2),
        (2, 1),
        (2, 0),
        (0, 0),
    ]


@pytest.mark.asyncio
async def test_grab_sequence_rejects_zero_count() -> None:
    camera = make_camera()
    with pytest.raises(ValueError):
        await camera.grab_sequence(0)


@pytest.mark.asyncio
async def test_grab_sequence_rejects_while_already_running() -> None:
    camera = make_camera()
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        await gate.wait()
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(3)
    with pytest.raises(exc.DeviceBusyError):
        await camera.grab_sequence(2)

    gate.set()
    assert camera._sequence_task is not None
    await camera._sequence_task


@pytest.mark.asyncio
async def test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() -> None:
    camera = make_camera()
    calls = 0
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        await gate.wait()
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(3)
    await asyncio.sleep(0)  # let the sequence task start and enter the first grab_data() call
    await camera.abort_sequence()

    # current (first) grab is still in flight, untouched by abort_sequence()
    assert calls == 1
    gate.set()
    assert camera._sequence_task is not None
    await camera._sequence_task

    # first grab was allowed to finish, but no second/third grab was started
    assert calls == 1
    assert camera._sequence_count_left == 0


@pytest.mark.asyncio
async def test_grab_sequence_waits_delay_between_grabs() -> None:
    camera = make_camera()
    calls = 0

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(2, delay=10)
    await asyncio.sleep(0)
    # first grab is done, second is now waiting out the delay
    assert calls == 1
    assert camera._sequence_task is not None
    assert not camera._sequence_task.done()

    # clean up the still-waiting background task instead of leaving its 10s timer pending
    await camera.abort_sequence()
    await camera._sequence_task


@pytest.mark.asyncio
async def test_grab_sequence_skips_delay_after_last_grab() -> None:
    camera = make_camera()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    camera.grab_data = fake_grab_data

    await asyncio.wait_for(camera.grab_sequence(1, delay=10), timeout=1.0)
    assert camera._sequence_task is not None
    await asyncio.wait_for(camera._sequence_task, timeout=1.0)


@pytest.mark.asyncio
async def test_grab_sequence_rejects_negative_delay() -> None:
    camera = make_camera()
    with pytest.raises(ValueError):
        await camera.grab_sequence(2, delay=-1)


@pytest.mark.asyncio
async def test_abort_sequence_cuts_delay_short() -> None:
    camera = make_camera()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(2, delay=10)
    await asyncio.sleep(0)  # let the first grab finish and enter the delay wait

    await asyncio.wait_for(camera.abort_sequence(), timeout=1.0)
    assert camera._sequence_task is not None
    await asyncio.wait_for(camera._sequence_task, timeout=1.0)  # would time out if delay wasn't cut short


@pytest.mark.asyncio
async def test_abort_cuts_delay_short() -> None:
    camera = make_camera()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(2, delay=10)
    await asyncio.sleep(0)  # let the first grab finish and enter the delay wait

    await camera.abort()
    assert camera._sequence_task is not None
    await asyncio.wait_for(camera._sequence_task, timeout=1.0)  # would time out if delay wasn't cut short


@pytest.mark.asyncio
async def test_abort_clears_running_sequence() -> None:
    camera = make_camera()
    calls = 0
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        await gate.wait()
        return "f.fits"

    camera.grab_data = fake_grab_data

    await camera.grab_sequence(3)
    await asyncio.sleep(0)  # let the sequence task start and enter the first grab_data() call
    assert calls == 1

    await camera.abort()
    assert camera._sequence_count_left == 0
    assert camera.expose_abort.is_set()

    # let the in-flight (mocked) grab return so the sequence task can wind down
    gate.set()
    assert camera._sequence_task is not None
    await camera._sequence_task
    assert calls == 1  # abort() prevented any further grabs from starting
