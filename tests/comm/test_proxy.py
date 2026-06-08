from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm.proxy import Proxy
from pyobs.interfaces import ICamera, IData, IExposureTime, IMode


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
    assert "get_exposure_time" in proxy.method_names
    assert "get_exposure_time_left" in proxy.method_names


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
    result = await proxy.execute("get_exposure_time")
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
    await proxy.set_mode("imaging", group=0)
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
