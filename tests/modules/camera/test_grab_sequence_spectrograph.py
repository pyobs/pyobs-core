"""Tests for BaseSpectrograph.grab_sequence()/abort_sequence(), the IDataSequence implementation
shared with BaseCamera via DataSequenceMixin (see test_grab_sequence.py for the camera side).

grab_data() itself is mocked out here -- these tests are about the sequencing logic
(grab_sequence/_run_sequence/abort_sequence/abort interplay and the pushed DataSequenceState),
not about exposure/VFS/FITS-header mechanics, which are exercised elsewhere.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from pyobs.interfaces import IDataSequence
from pyobs.modules.camera import DummySpectrograph
from pyobs.utils import exceptions as exc


def make_spectrograph() -> DummySpectrograph:
    spectrograph = DummySpectrograph()
    spectrograph.comm.set_state = AsyncMock()
    return spectrograph


@pytest.mark.asyncio
async def test_grab_sequence_returns_immediately() -> None:
    """grab_sequence() must not block for the whole sequence."""
    spectrograph = make_spectrograph()
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        await gate.wait()
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await asyncio.wait_for(spectrograph.grab_sequence(3), timeout=1.0)

    assert spectrograph._sequence_count_left == 3
    gate.set()
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task


@pytest.mark.asyncio
async def test_grab_sequence_runs_count_times() -> None:
    spectrograph = make_spectrograph()
    calls = 0

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(3)
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task

    assert calls == 3
    assert spectrograph._sequence_count_left == 0
    assert spectrograph._sequence_task is None


@pytest.mark.asyncio
async def test_grab_sequence_pushes_progressing_state() -> None:
    spectrograph = make_spectrograph()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(2)
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task

    pushed = [
        (call.args[1].count_total, call.args[1].count_left)
        for call in spectrograph.comm.set_state.call_args_list
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
    spectrograph = make_spectrograph()
    with pytest.raises(exc.InvalidArgumentError):
        await spectrograph.grab_sequence(0)


@pytest.mark.asyncio
async def test_grab_sequence_rejects_while_already_running() -> None:
    spectrograph = make_spectrograph()
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        await gate.wait()
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(3)
    with pytest.raises(exc.DeviceBusyError):
        await spectrograph.grab_sequence(2)

    gate.set()
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task


@pytest.mark.asyncio
async def test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() -> None:
    spectrograph = make_spectrograph()
    calls = 0
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        await gate.wait()
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(3)
    await asyncio.sleep(0)  # let the sequence task start and enter the first grab_data() call
    await spectrograph.abort_sequence()

    assert calls == 1
    gate.set()
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task

    assert calls == 1
    assert spectrograph._sequence_count_left == 0


@pytest.mark.asyncio
async def test_grab_sequence_waits_delay_between_grabs() -> None:
    spectrograph = make_spectrograph()
    calls = 0

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(2, delay=10)
    await asyncio.sleep(0)
    assert calls == 1
    assert spectrograph._sequence_task is not None
    assert not spectrograph._sequence_task.done()

    # clean up the still-waiting background task instead of leaving its 10s timer pending
    await spectrograph.abort_sequence()
    await spectrograph._sequence_task


@pytest.mark.asyncio
async def test_abort_sequence_cuts_delay_short() -> None:
    spectrograph = make_spectrograph()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(2, delay=10)
    await asyncio.sleep(0)  # let the first grab finish and enter the delay wait

    await asyncio.wait_for(spectrograph.abort_sequence(), timeout=1.0)
    assert spectrograph._sequence_task is not None
    await asyncio.wait_for(spectrograph._sequence_task, timeout=1.0)  # would time out if delay wasn't cut short


@pytest.mark.asyncio
async def test_abort_cuts_delay_short() -> None:
    """BaseSpectrograph.abort() must cut a pending inter-grab delay short too, same as
    BaseCamera.abort() -- see DataSequenceMixin._abort_data_sequence()."""
    spectrograph = make_spectrograph()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(2, delay=10)
    await asyncio.sleep(0)  # let the first grab finish and enter the delay wait

    await spectrograph.abort()
    assert spectrograph._sequence_task is not None
    await asyncio.wait_for(spectrograph._sequence_task, timeout=1.0)  # would time out if delay wasn't cut short


@pytest.mark.asyncio
async def test_abort_clears_running_sequence() -> None:
    spectrograph = make_spectrograph()
    calls = 0
    gate = asyncio.Event()

    async def fake_grab_data(broadcast: bool = True, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        await gate.wait()
        return "f.fits"

    spectrograph.grab_data = fake_grab_data

    await spectrograph.grab_sequence(3)
    await asyncio.sleep(0)  # let the sequence task start and enter the first grab_data() call
    assert calls == 1

    await spectrograph.abort()
    assert spectrograph._sequence_count_left == 0

    # let the in-flight (mocked) grab return so the sequence task can wind down
    gate.set()
    assert spectrograph._sequence_task is not None
    await spectrograph._sequence_task
    assert calls == 1  # abort() prevented any further grabs from starting
