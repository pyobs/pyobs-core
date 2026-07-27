"""Tests for FollowMixin's use of max_age when reading a followed device's position -- see
specs/plans/state-freshness-max-age.md."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm.proxy import Proxy
from pyobs.interfaces import AltAzState, IPointingAltAz, IPointingRaDec, RaDecState
from pyobs.mixins.follow import FollowMixin, get_coords
from pyobs.modules import Module


class _FollowingDevice(Module, FollowMixin, IPointingAltAz):
    def __init__(self, **kwargs: Any) -> None:
        Module.__init__(self, **kwargs)
        FollowMixin.__init__(self, mode=IPointingAltAz, **kwargs)

    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        pass


class _FakeProxyContext:
    """Minimal async context manager standing in for Object.proxy()'s _ProxyContext."""

    def __init__(self, proxy: object) -> None:
        self._proxy = proxy

    async def __aenter__(self) -> object:
        return self._proxy

    async def __aexit__(self, *exc: object) -> bool:
        return False


# ── get_coords ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_coords_altaz_passes_max_age_to_proxy() -> None:
    proxy = MagicMock(spec=Proxy)
    proxy.get_state = MagicMock(return_value=AltAzState(alt=10.0, az=20.0))

    result = await get_coords(proxy, IPointingAltAz, max_age=42.0)

    proxy.get_state.assert_called_once_with(IPointingAltAz, max_age=42.0)
    assert result == (10.0, 20.0)


@pytest.mark.asyncio
async def test_get_coords_radec_passes_max_age_to_proxy() -> None:
    proxy = MagicMock(spec=Proxy)
    proxy.get_state = MagicMock(return_value=RaDecState(ra=1.0, dec=2.0))

    result = await get_coords(proxy, IPointingRaDec, max_age=42.0)

    proxy.get_state.assert_called_once_with(IPointingRaDec, max_age=42.0)
    assert result == (1.0, 2.0)


@pytest.mark.asyncio
async def test_get_coords_raises_when_proxy_state_is_none() -> None:
    """Whether from "never published" or max_age making a stale value look absent, get_coords
    must raise -- callers (FollowMixin.__update_follow) rely on this to trigger their existing
    fail-safe backoff path."""
    proxy = MagicMock(spec=Proxy)
    proxy.get_state = MagicMock(return_value=None)

    with pytest.raises(ValueError):
        await get_coords(proxy, IPointingAltAz, max_age=42.0)


@pytest.mark.asyncio
async def test_get_coords_module_branch_ignores_max_age() -> None:
    """A Module's own state is read via get_own_state(), which has no max_age param -- it's
    always current from its own perspective."""
    module = MagicMock(spec=Module)
    module.comm.get_own_state = MagicMock(return_value=AltAzState(alt=5.0, az=6.0))

    result = await get_coords(module, IPointingAltAz, max_age=42.0)

    module.comm.get_own_state.assert_called_once_with(IPointingAltAz)
    assert result == (5.0, 6.0)


# ── FollowMixin ───────────────────────────────────────────────────────────────


def test_follow_max_age_defaults_to_3x_interval() -> None:
    device = _FollowingDevice(device=None, interval=100.0)
    assert getattr(device, "_FollowMixin__follow_max_age") == 300.0


def test_follow_max_age_respects_explicit_value() -> None:
    device = _FollowingDevice(device=None, interval=100.0, follow_max_age=17.0)
    assert getattr(device, "_FollowMixin__follow_max_age") == 17.0


@pytest.mark.asyncio
async def test_update_follow_passes_max_age_to_followed_device_state(mocker) -> None:  # type: ignore[no-untyped-def]
    device = _FollowingDevice(device="othertelescope", interval=100.0, follow_max_age=17.0)
    device.comm.get_own_state = MagicMock(return_value=AltAzState(alt=1.0, az=2.0))
    device.has_proxy = AsyncMock(return_value=True)

    fake_proxy = MagicMock(spec=Proxy)
    fake_proxy.get_state = MagicMock(return_value=AltAzState(alt=1.0, az=2.0))
    device.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))  # type: ignore[method-assign]

    # first sleep(10) before the loop returns normally; the interval sleep after the first
    # (and only) full iteration raises to break out of the otherwise-infinite loop
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))

    check = getattr(device, "_FollowMixin__update_follow")
    with pytest.raises(asyncio.CancelledError):
        await check()

    fake_proxy.get_state.assert_called_once_with(IPointingAltAz, max_age=17.0)


@pytest.mark.asyncio
async def test_update_follow_backs_off_when_followed_state_is_stale(mocker) -> None:  # type: ignore[no-untyped-def]
    """A None from get_coords() (stale or never-published) must hit the existing
    "could not fetch coordinates" fail-safe path, not raise out of the background task."""
    device = _FollowingDevice(device="othertelescope", interval=100.0, follow_max_age=17.0)
    device.comm.get_own_state = MagicMock(return_value=AltAzState(alt=1.0, az=2.0))
    device.has_proxy = AsyncMock(return_value=True)

    fake_proxy = MagicMock(spec=Proxy)
    fake_proxy.get_state = MagicMock(return_value=None)
    device.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))  # type: ignore[method-assign]

    # first sleep(10) before the loop, then the "could not fetch coordinates" backoff sleep
    # (interval * 10) raises to break out cleanly after exactly one attempt
    mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))

    check = getattr(device, "_FollowMixin__update_follow")
    with pytest.raises(asyncio.CancelledError):
        await check()

    fake_proxy.get_state.assert_called_once_with(IPointingAltAz, max_age=17.0)
