"""Integration tests for Phase 8 Access Control (ACLs) over real XMPP.

Verifies that a denied RPC call round-trips as an XMPP IQ `forbidden`
condition and surfaces as `exc.RemoteError` on the caller side, and that
an allowed call still succeeds normally.

Requires a live ejabberd server — see tests/xmpp/docker-compose.yml.
"""

from __future__ import annotations

import asyncio

import pytest

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import ICooling, IGain
from pyobs.modules.camera.dummycamera import DummyCamera
from pyobs.utils import exceptions as exc

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


async def wait_for(condition, *, timeout: float = 15.0, interval: float = 0.1) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


def make_camera_comm(xmpp_config) -> XmppComm:
    return XmppComm(
        user="camera",
        domain=xmpp_config.domain,
        password=xmpp_config.password,
        server=f"{xmpp_config.host}:{xmpp_config.port}",
        use_tls=xmpp_config.use_tls,
        ignore_cert_errors=xmpp_config.ignore_cert_errors,
    )


async def test_acl_deny_forbids_call(make_xmpp_comm, xmpp_config) -> None:
    """A caller on the "deny" list gets exc.RemoteError with a forbidden message, not a normal fault."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config), acl={"deny": ["observer"]})
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            async with observer_comm.proxy("camera", ICooling) as cam:
                with pytest.raises(exc.RemoteError) as exc_info:
                    await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert "forbidden" in str(exc_info.value).lower()

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_acl_allow_interface_name_sugar(make_xmpp_comm, xmpp_config) -> None:
    """Naming an interface under "allow" permits all of its methods, but nothing outside it."""

    async def _run():
        camera = DummyCamera(
            name="camera", comm=make_camera_comm(xmpp_config), acl={"allow": {"observer": ["ICooling"]}}
        )
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            # set_cooling is part of ICooling -- permitted via the interface-name sugar
            async with observer_comm.proxy("camera", ICooling) as cam:
                result = await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert result is None

            # set_gain is part of IGain -- not covered by the "ICooling" sugar entry
            async with observer_comm.proxy("camera", IGain) as cam:
                with pytest.raises(exc.RemoteError) as exc_info:
                    await cam.set_gain(42.0)
            assert "forbidden" in str(exc_info.value).lower()

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_acl_deny_allows_other_callers(make_xmpp_comm, xmpp_config) -> None:
    """A module not on the "deny" list is unaffected."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config), acl={"deny": ["legacy_gui"]})
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            async with observer_comm.proxy("camera", ICooling) as cam:
                result = await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert result is None

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_acl_allow_permits_listed_method(make_xmpp_comm, xmpp_config) -> None:
    """A caller granted "*" access under "allow" can still call normally."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config), acl={"allow": {"observer": "*"}})
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            async with observer_comm.proxy("camera", ICooling) as cam:
                result = await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert result is None

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_acl_allow_denies_unlisted_caller(make_xmpp_comm, xmpp_config) -> None:
    """A caller not present in the "allow" map is denied by default."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config), acl={"allow": {"mastermind": "*"}})
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            async with observer_comm.proxy("camera", ICooling) as cam:
                with pytest.raises(exc.RemoteError) as exc_info:
                    await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert "forbidden" in str(exc_info.value).lower()

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)
