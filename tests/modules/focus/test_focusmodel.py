import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.interfaces import (
    IFocusModel,
    ITemperatures,
    IWeather,
    OptimalFocusState,
    SensorReading,
    TemperaturesState,
    WeatherSensorReading,
)
from pyobs.modules import Module
from pyobs.modules.focus.focusmodel import FocusModel, MissingSensorError, WeatherDataError
from pyobs.utils.enums import WeatherSensors


class _FakeProxyContext:
    """Minimal async context manager standing in for Object.proxy()'s _ProxyContext."""

    def __init__(self, proxy: object) -> None:
        self._proxy = proxy

    async def __aenter__(self) -> object:
        return self._proxy

    async def __aexit__(self, *exc: object) -> bool:
        return False


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

    with pytest.raises(WeatherDataError):
        await fm._get_values()


# ── temp_max_age ──────────────────────────────────────────────────────────────


def test_temp_max_age_defaults_to_2x_interval() -> None:
    fm = FocusModel(model="dummy", interval=100)
    assert fm._temp_max_age == 200.0


def test_temp_max_age_respects_explicit_value() -> None:
    fm = FocusModel(model="dummy", interval=100, temp_max_age=42.0)
    assert fm._temp_max_age == 42.0


@pytest.mark.asyncio
async def test_get_values_passes_temp_max_age_to_wait_for_state() -> None:
    fm = FocusModel(model="dummy", temperatures={"temp": {"module": "sensors", "sensor": "M1"}}, temp_max_age=30.0)

    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(
        return_value=TemperaturesState(readings=[SensorReading(name="M1", value=12.3)])
    )
    fm.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))  # type: ignore[method-assign]

    values = await fm._get_values()

    fake_proxy.wait_for_state.assert_awaited_once_with(ITemperatures, max_age=30.0)
    assert values == {"temp": 12.3}


@pytest.mark.asyncio
async def test_get_values_treats_stale_temperature_as_missing() -> None:
    """None from wait_for_state() -- whether "never published" or "published but stale past
    max_age" -- must raise MissingSensorError, same as before this plan."""
    fm = FocusModel(model="dummy", temperatures={"temp": {"module": "sensors", "sensor": "M1"}}, temp_max_age=30.0)

    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(return_value=None)
    fm.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))  # type: ignore[method-assign]

    with pytest.raises(MissingSensorError):
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
async def test_open_publishes_placeholder_when_weather_unreachable(mocker, caplog) -> None:
    """weather is a string name that no proxy exists for yet (e.g. the weather module hasn't
    connected at this point in startup) -- open() must still publish some IFocusModel state
    instead of leaving it unpublished, so the module doesn't trip Module.startup()'s
    missing-published-state warning."""
    fm = FocusModel(weather="weather", model="temp")
    fm._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await fm.open()

    fm._comm.set_state.assert_awaited_once()
    interface, state = fm._comm.set_state.await_args[0]
    assert interface is IFocusModel
    assert isinstance(state, OptimalFocusState)
    assert state.focus == 0.0
    assert "Could not compute initial focus model state" in caplog.text


@pytest.mark.asyncio
async def test_update_publishes_state_every_iteration(mocker) -> None:
    weather = _weather_mock(5.0)
    fm = FocusModel(weather=weather, model="temp", interval=10)
    fm._comm.set_state = AsyncMock()

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
