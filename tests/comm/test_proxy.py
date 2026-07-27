from __future__ import annotations

import inspect
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest

from pyobs.comm.proxy import Proxy
from pyobs.interfaces import CoolingState, ICamera, ICooling, IData, IExposureTime, IMode
from pyobs.utils.time import Time


def make_proxy(interfaces: list, return_value: object = None) -> tuple[Proxy, MagicMock]:
    """Create a Proxy with a mock comm."""
    comm = MagicMock()
    comm.cast_to_simple_pre = []
    comm.cast_to_simple_post = []
    comm.execute = AsyncMock(return_value=return_value)
    proxy = Proxy(comm, "camera", interfaces)
    return proxy, comm


# ── construction ──────────────────────────────────────────────────────────────


def test_proxy_name() -> None:
    proxy, _ = make_proxy([IExposureTime])
    assert proxy.name == "camera"


def test_proxy_interfaces() -> None:
    proxy, _ = make_proxy([IExposureTime, IMode])
    assert IExposureTime in proxy.interfaces
    assert IMode in proxy.interfaces


def test_proxy_method_names() -> None:
    proxy, _ = make_proxy([IExposureTime])
    assert "set_exposure_time" in proxy.method_names


def test_proxy_deduplicates_parent_interfaces() -> None:
    """When ICamera and IData are given, IData is removed from interfaces since ICamera implements it."""
    proxy, _ = make_proxy([ICamera, IData])
    assert IData not in proxy.interfaces
    assert ICamera in proxy.interfaces
    # still accessible as instance of both
    assert isinstance(proxy, ICamera)
    assert isinstance(proxy, IData)


def test_proxy_is_instance_of_interfaces() -> None:
    proxy, _ = make_proxy([IExposureTime, IMode])
    assert isinstance(proxy, IExposureTime)
    assert isinstance(proxy, IMode)


# ── signature ─────────────────────────────────────────────────────────────────


def test_proxy_signature() -> None:
    proxy, _ = make_proxy([IExposureTime])
    sig = proxy.signature("set_exposure_time")
    assert isinstance(sig, inspect.Signature)
    assert "exposure_time" in sig.parameters


def test_proxy_interface_method() -> None:
    proxy, _ = make_proxy([IExposureTime])
    method = proxy.interface_method("set_exposure_time")
    assert callable(method)


# ── execute ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_calls_comm() -> None:
    proxy, comm = make_proxy([IExposureTime], return_value=None)
    await proxy.execute("set_exposure_time", 30.0)
    comm.execute.assert_called_once()
    call_args = comm.execute.call_args
    assert call_args[0][0] == "camera"
    assert call_args[0][1] == "set_exposure_time"


@pytest.mark.asyncio
async def test_execute_returns_value() -> None:
    proxy, _ = make_proxy([IExposureTime], return_value=30.0)
    result = await proxy.execute("set_exposure_time", 30.0)
    assert result == 30.0


@pytest.mark.asyncio
async def test_proxy_method_calls_execute() -> None:
    """Calling a method on the proxy goes through execute."""
    proxy, comm = make_proxy([IExposureTime], return_value=None)
    await proxy.set_exposure_time(30.0)
    comm.execute.assert_called_once()
    assert comm.execute.call_args[0][1] == "set_exposure_time"


@pytest.mark.asyncio
async def test_proxy_method_with_kwargs() -> None:
    proxy, comm = make_proxy([IMode], return_value=None)
    await proxy.set_mode("imaging", group="Instrument")
    comm.execute.assert_called_once()
    assert comm.execute.call_args[0][1] == "set_mode"


@pytest.mark.asyncio
async def test_execute_multiple_interfaces() -> None:
    """Methods from both interfaces are callable."""
    proxy, comm = make_proxy([IExposureTime, IMode], return_value=None)

    await proxy.set_exposure_time(10.0)
    assert comm.execute.call_args[0][1] == "set_exposure_time"

    comm.execute.reset_mock()
    await proxy.set_mode("spectroscopy")
    assert comm.execute.call_args[0][1] == "set_mode"


# ── state / max_age ───────────────────────────────────────────────────────────


def _cooling_state(age_seconds: float = 0.0) -> CoolingState:
    """A CoolingState timestamped `age_seconds` in the past."""
    return CoolingState(setpoint=-10.0, power=50, enabled=True, time=Time(Time.now() - age_seconds * u.second))


def test_get_state_no_max_age_returns_regardless_of_age() -> None:
    """Callers that don't pass max_age see no behavior change, however old the cached state."""
    proxy, _ = make_proxy([ICooling])
    proxy.update_state(ICooling, _cooling_state(age_seconds=1000.0))
    assert proxy.get_state(ICooling) is not None


def test_get_state_within_max_age_returns_state() -> None:
    proxy, _ = make_proxy([ICooling])
    proxy.update_state(ICooling, _cooling_state(age_seconds=1.0))
    assert proxy.get_state(ICooling, max_age=10.0) is not None


def test_get_state_older_than_max_age_returns_none() -> None:
    proxy, _ = make_proxy([ICooling])
    proxy.update_state(ICooling, _cooling_state(age_seconds=100.0))
    assert proxy.get_state(ICooling, max_age=10.0) is None


def test_get_state_none_when_never_published_regardless_of_max_age() -> None:
    proxy, _ = make_proxy([ICooling])
    assert proxy.get_state(ICooling, max_age=10.0) is None


def test_get_state_raises_for_state_without_time_field() -> None:
    """A future interface whose State dataclass has no `time` field fails loudly at the call
    site rather than max_age silently doing nothing."""

    class FakeStateWithoutTime:
        pass

    proxy, _ = make_proxy([ICooling])
    proxy.update_state(ICooling, FakeStateWithoutTime())
    with pytest.raises(ValueError, match="time"):
        proxy.get_state(ICooling, max_age=10.0)


@pytest.mark.asyncio
async def test_wait_for_state_returns_fresh_cached_value_immediately() -> None:
    proxy, comm = make_proxy([ICooling])
    comm.subscribe_state = AsyncMock()
    proxy.update_state(ICooling, _cooling_state(age_seconds=1.0))

    result = await proxy.wait_for_state(ICooling, max_age=10.0)

    assert result is not None
    comm.subscribe_state.assert_not_called()


@pytest.mark.asyncio
async def test_wait_for_state_treats_stale_cached_value_as_absent_and_waits() -> None:
    """A stale cached value doesn't short-circuit -- wait_for_state subscribes for a fresh
    update, the same as if nothing had been cached yet."""
    proxy, comm = make_proxy([ICooling])
    proxy.update_state(ICooling, _cooling_state(age_seconds=1000.0))

    async def fake_subscribe(client: str, interface: object, callback: Callable[[object], None]) -> None:
        callback(_cooling_state(age_seconds=0.0))

    comm.subscribe_state = AsyncMock(side_effect=fake_subscribe)
    comm.unsubscribe_state = AsyncMock()

    result = await proxy.wait_for_state(ICooling, timeout=1.0, max_age=10.0)

    assert result is not None
    comm.subscribe_state.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_state_returns_none_if_update_that_arrives_is_still_stale() -> None:
    """If the value that arrives during the wait is itself already older than max_age (e.g. a
    delayed/replayed publish), wait_for_state returns None rather than a nominally-new value
    that still fails the freshness bar."""
    proxy, comm = make_proxy([ICooling])

    async def fake_subscribe(client: str, interface: object, callback: Callable[[object], None]) -> None:
        callback(_cooling_state(age_seconds=1000.0))

    comm.subscribe_state = AsyncMock(side_effect=fake_subscribe)
    comm.unsubscribe_state = AsyncMock()

    result = await proxy.wait_for_state(ICooling, timeout=1.0, max_age=10.0)

    assert result is None


@pytest.mark.asyncio
async def test_wait_for_state_timeout_behavior_unchanged_by_max_age() -> None:
    proxy, comm = make_proxy([ICooling])
    comm.subscribe_state = AsyncMock()
    comm.unsubscribe_state = AsyncMock()

    result = await proxy.wait_for_state(ICooling, timeout=0.05, max_age=10.0)

    assert result is None
