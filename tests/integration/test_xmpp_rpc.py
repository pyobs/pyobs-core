"""Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).

Uses DummyCamera as the remote module under test. Verifies that all
value types round-trip correctly across the XMPP RPC path.

Note: tests use methods whose interface annotations match DummyCamera's
actual return types. Methods that return old types (tuple, dict) while the
interface now declares -> State will be covered once DummyCamera is updated
in Phase 3.

Requires a live ejabberd server — see tests/xmpp/docker-compose.yml.
"""

from __future__ import annotations

import asyncio

import pytest

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import IBinning, ICooling
from pyobs.modules.camera.dummycamera import DummyCamera

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


async def test_rpc_void_return_bool_float_params(make_xmpp_comm, xmpp_config) -> None:
    """set_cooling(bool, float) -> None: void return with bool + float params."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
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


async def test_rpc_float_return(make_xmpp_comm, xmpp_config) -> None:
    """get_gain() -> float: scalar float return."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            from pyobs.interfaces import IGain

            async with observer_comm.proxy("camera", IGain) as cam:
                result = await cam.get_gain()

            assert isinstance(result, float)

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_rpc_float_param_float_return(make_xmpp_comm, xmpp_config) -> None:
    """set_gain(float) then get_gain() -> float: float param and return."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            from pyobs.interfaces import IGain

            async with observer_comm.proxy("camera", IGain) as cam:
                await cam.set_gain(42.0)
                result = await cam.get_gain()

            assert result == pytest.approx(42.0)

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_rpc_int_params_void_return(make_xmpp_comm, xmpp_config) -> None:
    """set_binning(int, int) -> None: multiple int params, void return."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            async with observer_comm.proxy("camera", IBinning) as cam:
                result = await cam.set_binning(2, 2)
            assert result is None

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_rpc_exception_fault(make_xmpp_comm, xmpp_config) -> None:
    """Calling a method that raises on the remote side propagates the exception."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            import pyobs.utils.exceptions as exc
            from pyobs.interfaces import IExposure

            async with observer_comm.proxy("camera", IExposure) as cam:
                # abort_exposure when not exposing should raise
                with pytest.raises((exc.RemoteError, exc.InvocationError, Exception)):
                    await cam.abort_exposure()

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_rpc_bool_float_roundtrip(make_xmpp_comm, xmpp_config) -> None:
    """set_cooling(bool, float) then verify via state: full encode/decode cycle."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()
            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok

            received = []
            await observer_comm.subscribe_state("camera", ICooling, received.append)

            async with observer_comm.proxy("camera", ICooling) as cam:
                await cam.set_cooling(enabled=True, setpoint=-30.0)

            # Wait for the new setpoint to appear in state
            assert await wait_for(
                lambda: any(s.setpoint == pytest.approx(-30.0) for s in received),
                timeout=5.0,
            ), "State did not reflect new setpoint after set_cooling RPC"

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)
