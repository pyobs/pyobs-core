from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.interfaces import AutoFocusResult, AutoFocusState, IAutoFocus
from pyobs.modules import Module
from pyobs.modules.focus.focusseries import AutoFocusSeries
from pyobs.utils.focusseries import FocusSeries


def _series() -> AutoFocusSeries:
    return AutoFocusSeries(focuser="focuser", camera="camera", series=MagicMock(spec=FocusSeries))


@pytest.mark.asyncio
async def test_open_publishes_initial_state(mocker) -> None:
    series = _series()
    series._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await series.open()

    series._comm.set_state.assert_awaited_once()
    interface, state = series._comm.set_state.await_args[0]
    assert interface is IAutoFocus
    assert isinstance(state, AutoFocusState)
    assert state.points == []


@pytest.mark.asyncio
async def test_auto_focus_wraps_tuple_result_in_autofocusresult() -> None:
    series = _series()
    series._auto_focus = AsyncMock(return_value=(12.3, 0.05))

    result = await series.auto_focus(5, 0.1, 2.0)

    series._auto_focus.assert_awaited_once_with(5, 0.1, 2.0)
    assert result == AutoFocusResult(focus=12.3, focus_err=0.05)


@pytest.mark.asyncio
async def test_auto_focus_resets_running_flag_on_error() -> None:
    series = _series()
    series._auto_focus = AsyncMock(side_effect=ValueError("boom"))

    with pytest.raises(ValueError):
        await series.auto_focus(5, 0.1, 2.0)

    assert series._running is False


def test_focus_series_get_data_points_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        FocusSeries().get_data_points()
