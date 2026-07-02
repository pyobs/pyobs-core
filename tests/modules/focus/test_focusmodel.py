import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.interfaces import IFocusModel, IWeather, OptimalFocusState, WeatherSensorReading
from pyobs.modules import Module
from pyobs.modules.focus.focusmodel import FocusModel
from pyobs.utils.enums import WeatherSensors


def _weather_mock(value: float | None) -> MagicMock:
    weather = MagicMock(spec=IWeather)
    weather.get_sensor_value = AsyncMock(
        return_value=WeatherSensorReading(sensor=WeatherSensors.TEMPERATURE, value=value, unit="celsius")
    )
    return weather


@pytest.mark.asyncio
async def test_get_values_extracts_reading_value() -> None:
    weather = _weather_mock(5.0)
    fm = FocusModel(weather=weather, model="temp")

    values = await fm._get_values()

    assert values == {"temp": 5.0}
    weather.get_sensor_value.assert_awaited_once_with(fm._temp_station, fm._temp_sensor)


@pytest.mark.asyncio
async def test_get_values_raises_on_none_value() -> None:
    weather = _weather_mock(None)
    fm = FocusModel(weather=weather, model="temp")

    with pytest.raises(ValueError):
        await fm._get_values()


@pytest.mark.asyncio
async def test_open_publishes_optimal_focus_state(mocker) -> None:
    weather = _weather_mock(5.0)
    fm = FocusModel(weather=weather, model="temp")
    fm._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await fm.open()

    fm._comm.set_state.assert_awaited_once()
    interface, state = fm._comm.set_state.await_args[0]
    assert interface is IFocusModel
    assert isinstance(state, OptimalFocusState)
    assert state.focus == 5.0


@pytest.mark.asyncio
async def test_update_publishes_state_every_iteration(mocker) -> None:
    weather = _weather_mock(5.0)
    fm = FocusModel(weather=weather, model="temp", interval=10)
    fm._comm.set_state = AsyncMock()
    fm._enabled = True

    # first sleep(1) before the loop returns normally, the interval sleep after
    # the first iteration (focuser proxy is unset, so has_proxy is False) raises
    # to break out of the otherwise-infinite loop
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))

    with pytest.raises(asyncio.CancelledError):
        await fm._update()

    fm._comm.set_state.assert_awaited_once()
    interface, state = fm._comm.set_state.await_args[0]
    assert interface is IFocusModel
    assert state.focus == 5.0
