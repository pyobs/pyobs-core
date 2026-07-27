"""Tests for WeatherAwareMixin's use of Proxy.wait_for_state's max_age -- see
specs/plans/state-freshness-max-age.md."""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.interfaces import IWeather, WeatherState
from pyobs.modules.roof import DummyRoof


class _FakeProxyContext:
    """Minimal async context manager standing in for Object.proxy()'s _ProxyContext."""

    def __init__(self, proxy: object) -> None:
        self._proxy = proxy

    async def __aenter__(self) -> object:
        return self._proxy

    async def __aexit__(self, *exc: object) -> bool:
        return False


async def _run_one_weather_check_iteration(roof: DummyRoof, fake_proxy: object) -> None:
    """Runs WeatherAwareMixin's private background-check loop just long enough for one
    iteration (it blocks on asyncio.sleep(10) between iterations), then cancels it."""
    roof.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))  # type: ignore[method-assign]

    check = getattr(roof, "_WeatherAwareMixin__weather_check")
    task = asyncio.create_task(check())
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_weather_check_passes_default_max_age_to_wait_for_state() -> None:
    roof = DummyRoof(weather="weatherstation")
    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(return_value=WeatherState(good=True))

    await _run_one_weather_check_iteration(roof, fake_proxy)

    fake_proxy.wait_for_state.assert_called_once_with(IWeather, timeout=5.0, max_age=120.0)


@pytest.mark.asyncio
async def test_weather_check_passes_configured_max_age_to_wait_for_state() -> None:
    roof = DummyRoof(weather="weatherstation", weather_max_age=30.0)
    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(return_value=WeatherState(good=True))

    await _run_one_weather_check_iteration(roof, fake_proxy)

    fake_proxy.wait_for_state.assert_called_once_with(IWeather, timeout=5.0, max_age=30.0)


@pytest.mark.asyncio
async def test_weather_check_treats_none_from_wait_for_state_as_bad_weather() -> None:
    """None from wait_for_state() -- whether "never published" or "published but stale past
    max_age" -- must be treated as bad weather (fail-safe), same as before this plan."""
    roof = DummyRoof(weather="weatherstation", weather_max_age=30.0)
    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(return_value=None)

    await _run_one_weather_check_iteration(roof, fake_proxy)

    assert roof.is_weather_good() is False


@pytest.mark.asyncio
async def test_weather_check_treats_fresh_good_state_as_good_weather() -> None:
    roof = DummyRoof(weather="weatherstation", weather_max_age=30.0)
    fake_proxy = AsyncMock()
    fake_proxy.wait_for_state = AsyncMock(return_value=WeatherState(good=True))

    await _run_one_weather_check_iteration(roof, fake_proxy)

    assert roof.is_weather_good() is True
