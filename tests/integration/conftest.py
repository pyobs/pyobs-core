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


@pytest_asyncio.fixture
async def make_xmpp_comm(xmpp_config: XmppConfig):
    """
    Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm
    for ``<user>@<domain>``.  Optionally pass a module stub as the second
    argument.  All comms are closed after the test.
    """
    from pyobs.comm.xmpp.xmppcomm import XmppComm

    opened: list[XmppComm] = []

    async def _factory(user: str, module=None) -> XmppComm:
        comm = XmppComm(
            user=user,
            domain=xmpp_config.domain,
            password=xmpp_config.password,
            server=f"{xmpp_config.host}:{xmpp_config.port}",
            use_tls=xmpp_config.use_tls,
            ignore_cert_errors=xmpp_config.ignore_cert_errors,
        )
        if module is not None:
            comm.module = module
            module._comm = comm
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
