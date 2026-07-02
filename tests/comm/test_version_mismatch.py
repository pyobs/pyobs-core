"""Tests for the mixed-version-fleet diagnostic on interface resolution.

Covers the versioned `urn:pyobs:interface:{name}:{version}` feature filtering in
XmppComm._get_interfaces, the XmppComm._diagnose_missing_interface hook, and
Comm._resolve_proxy folding that hint into its ValueError.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm.comm import Comm
from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import ICooling, IModule


class FakeInterface:
    """Stand-in for a pyobs Interface class -- only __name__ and .version matter here."""

    version = 1


def make_xmpp_comm() -> XmppComm:
    """Create a minimal XmppComm instance for testing, without a live connection."""
    comm = XmppComm.__new__(XmppComm)
    comm._xmpp = MagicMock()
    comm._domain = "localhost"
    comm._resource = "pyobs"
    comm._interface_features = {}
    comm._warned_version_mismatches = set()
    return comm


# ---------------------------------------------------------------------------
# XmppComm._get_interfaces: versioned feature filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_interfaces_keeps_matching_version() -> None:
    comm = make_xmpp_comm()
    features = ["urn:pyobs:interface:IModule:1", "urn:pyobs:interface:ICooling:1"]
    comm._safe_send = AsyncMock(return_value={"features": features})

    names = await comm._get_interfaces("camera@localhost/pyobs")

    assert "ICooling" in names
    assert "IModule" in names


@pytest.mark.asyncio
async def test_get_interfaces_drops_mismatched_version() -> None:
    comm = make_xmpp_comm()
    features = ["urn:pyobs:interface:IModule:1", "urn:pyobs:interface:ICooling:2"]
    comm._safe_send = AsyncMock(return_value={"features": features})

    names = await comm._get_interfaces("camera@localhost/pyobs")

    assert "IModule" in names
    assert "ICooling" not in names


@pytest.mark.asyncio
async def test_get_interfaces_drops_unknown_name() -> None:
    comm = make_xmpp_comm()
    features = ["urn:pyobs:interface:IModule:1", "urn:pyobs:interface:INotReal:1"]
    comm._safe_send = AsyncMock(return_value={"features": features})

    names = await comm._get_interfaces("camera@localhost/pyobs")

    assert "IModule" in names
    assert "INotReal" not in names


@pytest.mark.asyncio
async def test_get_interfaces_caches_raw_features_regardless_of_match() -> None:
    """The raw feature list is cached even for names that get filtered out --
    _diagnose_missing_interface needs the mismatched entry still present."""
    comm = make_xmpp_comm()
    features = ["urn:pyobs:interface:IModule:1", "urn:pyobs:interface:ICooling:2"]
    comm._safe_send = AsyncMock(return_value={"features": features})

    await comm._get_interfaces("camera@localhost/pyobs")

    assert comm._interface_features["camera@localhost/pyobs"] == features


# ---------------------------------------------------------------------------
# XmppComm._diagnose_missing_interface
# ---------------------------------------------------------------------------


def test_diagnose_returns_none_when_nothing_published() -> None:
    comm = make_xmpp_comm()
    comm._interface_features["camera@localhost/pyobs"] = []

    assert comm._diagnose_missing_interface("camera", FakeInterface) is None


def test_diagnose_returns_none_for_unknown_client() -> None:
    comm = make_xmpp_comm()

    assert comm._diagnose_missing_interface("camera", FakeInterface) is None


def test_diagnose_remote_ahead_suggests_upgrading_client() -> None:
    comm = make_xmpp_comm()
    comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:2"]

    hint = comm._diagnose_missing_interface("camera", FakeInterface)

    assert hint is not None
    assert "v2" in hint
    assert "v1" in hint
    assert "upgrade this client" in hint


def test_diagnose_remote_behind_suggests_upgrading_remote() -> None:
    comm = make_xmpp_comm()
    comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:0"]

    hint = comm._diagnose_missing_interface("camera", FakeInterface)

    assert hint is not None
    assert "upgrade the remote module" in hint


def test_diagnose_logs_once_per_client_interface_pair(caplog: pytest.LogCaptureFixture) -> None:
    comm = make_xmpp_comm()
    comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:2"]

    with caplog.at_level(logging.WARNING):
        comm._diagnose_missing_interface("camera", FakeInterface)
        comm._diagnose_missing_interface("camera", FakeInterface)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Comm._resolve_proxy: folding the hint into the ValueError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_proxy_appends_diagnostic_hint() -> None:
    comm = Comm.__new__(Comm)
    comm._get_client = AsyncMock(return_value=object())
    comm._diagnose_missing_interface = MagicMock(return_value="Remote implements it at v2, upgrade this client.")

    with pytest.raises(ValueError, match="Remote implements it at v2"):
        await comm._resolve_proxy("camera", FakeInterface)

    comm._diagnose_missing_interface.assert_called_once_with("camera", FakeInterface)


@pytest.mark.asyncio
async def test_resolve_proxy_keeps_generic_message_when_no_hint() -> None:
    """Base Comm._diagnose_missing_interface returns None -- e.g. LocalComm, which can't
    have a version mismatch since it shares the same in-process class."""
    comm = Comm.__new__(Comm)
    comm._get_client = AsyncMock(return_value=object())

    with pytest.raises(ValueError) as exc_info:
        await comm._resolve_proxy("camera", FakeInterface)

    assert "is not of requested type" in str(exc_info.value)
    assert "Remote implements" not in str(exc_info.value)


def test_real_interfaces_default_to_version_one() -> None:
    """Sanity check that ICooling/IModule (used above as real interfaces) still have
    the expected default version, since the filtering tests depend on it."""
    assert ICooling.version == 1
    assert IModule.version == 1
