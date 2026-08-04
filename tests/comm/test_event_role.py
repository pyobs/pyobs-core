"""Tests for XmppComm's disco#info event role tagging.

See specs/plans/event-role-advertising.md -- disco#info previously advertised a module's sent
and subscribed events as one undifferentiated set, so consumers with no access to the
pyobs.events catalog (e.g. pyobs-web-client) couldn't tell producers from consumers.
"""

from __future__ import annotations

from pyobs.comm.xmpp.xmppcomm import _event_role
from pyobs.events import LogEvent, ModuleOpenedEvent


def test_event_role_send_only() -> None:
    assert _event_role(ModuleOpenedEvent, {ModuleOpenedEvent}, set()) == "send"


def test_event_role_subscribe_only() -> None:
    assert _event_role(ModuleOpenedEvent, set(), {ModuleOpenedEvent}) == "subscribe"


def test_event_role_send_and_subscribe() -> None:
    assert _event_role(ModuleOpenedEvent, {ModuleOpenedEvent}, {ModuleOpenedEvent}) == "send subscribe"


def test_event_role_ignores_unrelated_events() -> None:
    assert _event_role(ModuleOpenedEvent, {LogEvent}, {LogEvent}) == ""
