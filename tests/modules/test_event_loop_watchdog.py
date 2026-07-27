"""Module._watch_event_loop_lag: logs once when a stall starts and once when it clears,
never on every check while a stall persists."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.modules import Module


@pytest.mark.asyncio
async def test_no_lag_logs_nothing(mocker) -> None:
    m = Module()
    warning = mocker.patch("pyobs.modules.module.log.warning")
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))
    fake_loop = MagicMock()
    fake_loop.time.side_effect = [0.0, 1.0]  # exactly the requested interval -- no lag
    mocker.patch("asyncio.get_running_loop", return_value=fake_loop)

    with pytest.raises(asyncio.CancelledError):
        await m._watch_event_loop_lag()

    warning.assert_not_called()


@pytest.mark.asyncio
async def test_sustained_stall_logs_once_not_per_check(mocker) -> None:
    m = Module()
    warning = mocker.patch("pyobs.modules.module.log.warning")
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, None, asyncio.CancelledError()]))
    fake_loop = MagicMock()
    # interval is 1.0s each time, but 2.0s actually elapse -> 1.0s lag, twice in a row
    fake_loop.time.side_effect = [0.0, 2.0, 4.0]
    mocker.patch("asyncio.get_running_loop", return_value=fake_loop)

    with pytest.raises(asyncio.CancelledError):
        await m._watch_event_loop_lag()

    assert warning.call_count == 1
    assert "stalled" in warning.call_args[0][0]


@pytest.mark.asyncio
async def test_recovery_after_stall_logs_total_duration(mocker) -> None:
    m = Module()
    warning = mocker.patch("pyobs.modules.module.log.warning")
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, None, asyncio.CancelledError()]))
    fake_loop = MagicMock()
    # stall for one check (0.0 -> 2.0, 1.0s lag), then back to on-time (2.0 -> 3.0, no lag)
    fake_loop.time.side_effect = [0.0, 2.0, 3.0]
    mocker.patch("asyncio.get_running_loop", return_value=fake_loop)

    with pytest.raises(asyncio.CancelledError):
        await m._watch_event_loop_lag()

    assert warning.call_count == 2
    assert "stalled" in warning.call_args_list[0][0][0]
    assert "recovered" in warning.call_args_list[1][0][0]
    assert warning.call_args_list[1][0][1] == pytest.approx(3.0)
