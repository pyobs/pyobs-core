"""Integration test for DummyCamera state publishing via XEP-0060."""

from __future__ import annotations

import asyncio

import pytest

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import ICooling, IModule, IWindow
from pyobs.modules.camera.dummycamera import DummyCamera

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


async def wait_for(condition, *, timeout: float = 15.0, interval: float = 0.1) -> bool:
    """Poll *condition* until truthy or *timeout* seconds elapse."""
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


async def test_dummy_camera_publishes_cooling_state(make_xmpp_comm, xmpp_config) -> None:
    """
    DummyCamera's _cooling_thread publishes CoolingState every second.
    An observer subscribing to the camera's ICooling state must receive
    updates with sensible values.
    """

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()

            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok, "camera did not appear in observer's client list"

            received: list = []
            await observer_comm.subscribe_state("camera", ICooling, received.append)

            # Wait for at least 3 updates — cooling thread publishes every 1s
            assert await wait_for(
                lambda: len(received) >= 3, timeout=10.0
            ), f"Expected >= 3 state updates, got {len(received)}."

            last = received[-1]
            assert last.setpoint == pytest.approx(-10.0)
            assert 0 <= last.power <= 100
            assert last.enabled is True

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_dummy_camera_cooling_state_reflects_set_cooling(make_xmpp_comm, xmpp_config) -> None:
    """
    After calling set_cooling via RPC, the published CoolingState must
    reflect the new setpoint and enabled flag within the next publish cycle.
    """

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()

            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok, "camera did not appear in observer's client list"

            received: list = []
            await observer_comm.subscribe_state("camera", ICooling, received.append)

            assert await wait_for(lambda: len(received) >= 1, timeout=5.0), "No initial ICooling state received"

            async with observer_comm.proxy("camera", ICooling) as cam_cooling:
                await cam_cooling.set_cooling(enabled=True, setpoint=-25.0)

            # _cooling_thread publishes every 1s — give it up to 3 cycles to reflect
            # the new setpoint (one cycle may already be in flight with the old value)
            assert await wait_for(
                lambda: any(s.setpoint == pytest.approx(-25.0) for s in received),
                timeout=10.0,
            ), "CoolingState setpoint did not update to -25.0 after set_cooling RPC"

            matching = [s for s in received if s.setpoint == pytest.approx(-25.0)]
            assert matching[-1].enabled is True

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_dummy_camera_publishes_iwindow_capabilities(make_xmpp_comm, xmpp_config) -> None:
    """DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full frame."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()

            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok, "camera did not appear in observer's client list"

            caps = await observer_comm.get_capabilities("camera", IWindow)

            assert caps is not None, "IWindow.Capabilities not found in disco#info"
            assert isinstance(caps, IWindow.Capabilities)
            assert caps.full_frame.width > 0, "full_frame.width should be > 0"
            assert caps.full_frame.height > 0, "full_frame.height should be > 0"
            assert caps.full_frame.x == 0
            assert caps.full_frame.y == 0

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_dummy_camera_publishes_imodule_capabilities(make_xmpp_comm, xmpp_config) -> None:
    """DummyCamera.open() must publish IModule.Capabilities with version and label."""

    async def _run():
        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()

            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok, "camera did not appear in observer's client list"

            caps = await observer_comm.get_capabilities("camera", IModule)

            assert caps is not None, "IModule.Capabilities not found in disco#info"
            assert isinstance(caps, IModule.Capabilities)
            assert isinstance(caps.version, str) and len(caps.version) > 0
            assert isinstance(caps.label, str)

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)


async def test_dummy_camera_no_capabilities_for_unconfigured_interface(make_xmpp_comm, xmpp_config) -> None:
    """get_capabilities() must return None for an interface DummyCamera doesn't publish."""

    async def _run():
        from pyobs.interfaces import IFocuser

        camera = DummyCamera(name="camera", comm=make_camera_comm(xmpp_config))
        try:
            await camera.open()

            observer_comm = await make_xmpp_comm("observer")
            ok = await wait_for(lambda: "camera" in observer_comm.clients)
            assert ok, "camera did not appear in observer's client list"

            caps = await observer_comm.get_capabilities("camera", IFocuser)
            assert caps is None, "IFocuser.Capabilities should not be published by DummyCamera"

        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)
