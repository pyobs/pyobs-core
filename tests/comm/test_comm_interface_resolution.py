"""Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that resolves
wire-level interface names (used by XmppComm) via the interface registry.
"""

from __future__ import annotations

import logging
from abc import ABCMeta

import pytest

from pyobs.comm.comm import Comm
from pyobs.interfaces import ICamera, IModule, Interface


def test_resolves_known_core_interfaces() -> None:
    result = Comm._interface_names_to_classes(["ICamera", "IModule"])

    assert result == [ICamera, IModule]


def test_resolves_external_interface() -> None:
    """An interface defined entirely outside pyobs.interfaces resolves the same way
    core interfaces do -- this is what makes external-package interfaces work."""

    class IResolutionTestExternal(Interface, metaclass=ABCMeta):
        pass

    result = Comm._interface_names_to_classes(["IResolutionTestExternal"])

    assert result == [IResolutionTestExternal]


def test_skips_unknown_name(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        result = Comm._interface_names_to_classes(["INoSuchResolutionTestInterface"])

    assert result == []
    assert any("INoSuchResolutionTestInterface" in r.message for r in caplog.records)


def test_resolves_known_and_skips_unknown_in_same_list(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        result = Comm._interface_names_to_classes(["ICamera", "INoSuchResolutionTestInterface", "IModule"])

    assert result == [ICamera, IModule]
