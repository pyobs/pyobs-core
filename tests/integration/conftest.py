"""Fixtures shared across all integration tests."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

import pytest
import pytest_asyncio

from pyobs.comm.local.localnetwork import LocalNetwork

# ---------------------------------------------------------------------------
# LocalComm helpers (used by non-XMPP integration tests)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_network():
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


def connect(module, name: str):
    """Connect a module to LocalComm and return the comm."""
    from pyobs.comm.local.localcomm import LocalComm

    comm = LocalComm(name)
    comm.module = module
    module._comm = comm
    return comm


# ---------------------------------------------------------------------------
# XMPP helpers
#
# Connection details come from environment variables:
#   PYOBS_TEST_XMPP_HOST          hostname of the ejabberd server (required)
#   PYOBS_TEST_XMPP_DOMAIN        XMPP domain          (default: PYOBS_TEST_XMPP_HOST)
#   PYOBS_TEST_XMPP_PORT          port                 (default: 5222)
#   PYOBS_TEST_XMPP_PASSWORD      shared test password (default: pyobs)
#   PYOBS_TEST_XMPP_TLS           use TLS              (default: 1; set to 0 to disable)
#   PYOBS_TEST_XMPP_IGNORE_CERT   ignore cert errors   (default: 1; set to 0 to enforce)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class XmppConfig:
    host: str
    domain: str
    port: int
    password: str
    use_tls: bool
    ignore_cert_errors: bool


@pytest.fixture(scope="session")
def xmpp_config() -> XmppConfig:
    host = os.environ["PYOBS_TEST_XMPP_HOST"]
    return XmppConfig(
        host=host,
        domain=os.environ.get("PYOBS_TEST_XMPP_DOMAIN", host),
        port=int(os.environ.get("PYOBS_TEST_XMPP_PORT", "5222")),
        password=os.environ.get("PYOBS_TEST_XMPP_PASSWORD", "pyobs"),
        use_tls=os.environ.get("PYOBS_TEST_XMPP_TLS", "1") == "1",
        ignore_cert_errors=os.environ.get("PYOBS_TEST_XMPP_IGNORE_CERT", "1") == "1",
    )


@pytest.fixture
def make_unopened_comm(xmpp_config: XmppConfig):
    """Factory fixture: ``make_unopened_comm(user)`` returns an unopened XmppComm
    for ``<user>@<domain>``, for constructor-injecting into a module (real or
    stub) before anything is opened or connected."""
    from pyobs.comm.xmpp.xmppcomm import XmppComm

    def _factory(user: str) -> XmppComm:
        return XmppComm(
            user=user,
            domain=xmpp_config.domain,
            password=xmpp_config.password,
            server=f"{xmpp_config.host}:{xmpp_config.port}",
            use_tls=xmpp_config.use_tls,
            ignore_cert_errors=xmpp_config.ignore_cert_errors,
        )

    return _factory


@pytest.fixture
def make_camera_comm(make_unopened_comm):
    """Build an unopened XmppComm for user "camera", for constructor-injecting
    into DummyCamera(comm=...) -- the caller opens it via camera.open()."""
    return make_unopened_comm("camera")


def make_module(interfaces: list, comm, label: str = "Test Camera"):
    """Minimal module stub satisfying what XmppComm needs on connect.

    IModule must be included: XmppComm._get_interfaces() only adds a peer to
    _online_clients once it sees IModule in the disco#info features -- without
    it the peer never appears in comm.clients regardless of other interfaces.

    Takes comm (built via make_unopened_comm) rather than being retrofitted
    onto afterward, mirroring how a real module wires up: comm is known before
    the module is done configuring itself.
    """
    from unittest.mock import AsyncMock, MagicMock

    from pyobs.interfaces import IModule

    m = MagicMock()
    # Always include IModule so _got_online completes successfully
    m.interfaces = list({IModule} | set(interfaces))
    m.name = "camera"
    m._label = label
    m.get_label = AsyncMock(return_value=label)
    m.get_version = AsyncMock(return_value="2.0.0.dev1")
    m._comm = comm
    comm.module = m
    return m


@pytest_asyncio.fixture
async def make_xmpp_comm(xmpp_config: XmppConfig, make_unopened_comm):
    """
    Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm
    for ``<user>@<domain>``, building one via make_unopened_comm(user). Pass
    comm=<already-built-comm> to open a comm that was constructed (and wired
    to a module) earlier instead. All comms are closed after the test.
    """
    from pyobs.comm.xmpp.xmppcomm import XmppComm

    opened: list[XmppComm] = []

    async def _factory(user: str, comm: XmppComm | None = None) -> XmppComm:
        if comm is None:
            comm = make_unopened_comm(user)
        await comm.open()
        for _ in range(50):
            if comm._connected:
                break
            await asyncio.sleep(0.1)
        else:
            raise TimeoutError(f"{user}@{xmpp_config.domain} did not connect within 5 s")
        opened.append(comm)
        return comm

    yield _factory

    for comm in reversed(opened):
        try:
            await comm.close()
        except Exception:
            pass
