"""Tests for specs/plans/2026-08-28-precreate-pubsub-nodes.md.

Phase 1: XmppComm pre-creates its own event nodes at startup (_create_node, wired into
_register_events' send-only-declaration branch) so a subscriber doesn't have to wait for the
first publish. State nodes are explicitly out of scope (see the plan's "Why state nodes are
excluded" section) -- only event-node pre-creation is covered here.

Phase 2 (issue #824): _retry_delay's exponent must not overflow at large attempt counts, and
both retry-subscribe background tasks (_subscribe_event_with_retry for events,
_subscribe_with_retry for state) must discard their tracked key/handler on an unexpected
(non-IqError/IqTimeout) failure instead of leaving a permanently stuck "subscribed" marker
behind with nothing actually subscribed and nothing retrying.

Pure unit tests: no network, no live ejabberd.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import slixmpp.exceptions

from pyobs.comm.xmpp.xmppcomm import XmppComm, _retry_delay
from pyobs.events import LogEvent
from pyobs.interfaces import ICooling


def _make_comm() -> XmppComm:
    return XmppComm(jid="user@example.com")


def _fake_iq_error(condition: str = "conflict") -> slixmpp.exceptions.IqError:
    return slixmpp.exceptions.IqError({"error": {"condition": condition, "text": "", "type": "cancel"}})


def _make_fake_xmpp() -> MagicMock:
    """A fake XmppClient exposing distinguishable plugin method objects.

    Real method identity matters for these tests (asserting _safe_send was called with the
    right underlying plugin method), so plugin/method attributes are plain MagicMocks stored
    in a real dict rather than relying on MagicMock's auto-generated (and not reliably
    per-key-stable) __getitem__.
    """
    xmpp = MagicMock()
    xmpp.plugin = {
        "xep_0030": SimpleNamespace(add_feature=MagicMock()),
        "xep_0060": SimpleNamespace(
            create_node=MagicMock(name="create_node"),
            subscribe=MagicMock(name="subscribe"),
            unsubscribe=MagicMock(name="unsubscribe"),
            get_items=MagicMock(name="get_items"),
            publish=MagicMock(name="publish"),
        ),
        "xep_0115": SimpleNamespace(update_caps=MagicMock(name="update_caps")),
    }
    return xmpp


class TestRetryDelayOverflow:
    """#824: _retry_delay(attempt) overflowed (OverflowError) once 2**attempt exceeded float
    range, killing the retry task and leaving its tracked key permanently "subscribed"."""

    @pytest.mark.parametrize("attempt", [1024, 10**6])
    def test_does_not_overflow_at_high_attempt_counts(self, attempt: int) -> None:
        delay = _retry_delay(attempt)
        assert isinstance(delay, float)
        assert 0.0 <= delay <= 30.0

    def test_normal_attempt_counts_unaffected(self) -> None:
        # low attempts must still be able to return up to the cap -- the clamp must not
        # itself change behavior for realistic attempt counts.
        for attempt in range(0, 10):
            delay = _retry_delay(attempt)
            assert 0.0 <= delay <= 30.0


def test_event_node_naming_unchanged() -> None:
    node = XmppComm._event_node("camera", LogEvent)
    assert node == f"pyobs:event:camera:LogEvent:{LogEvent.version}"


class TestCreateNode:
    """_create_node calls create_node directly (no existence pre-check -- confirmed via a live
    repro against the test ejabberd that create_node's error reply is delivered normally as an
    IqError even with XmppComm's pubsub-event message Callback registered on the stream) and
    swallows the realistic failure modes so a permission denial or a <conflict/> on restart
    degrades gracefully to today's lazy auto-create rather than blocking startup."""

    @pytest.mark.asyncio
    async def test_sends_create_node_to_pubsub_service(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        node = "pyobs:event:camera:LogEvent:1"
        safe_send = AsyncMock(return_value=None)
        with patch.object(comm, "_safe_send", safe_send):
            await comm._create_node(node)
        create_node = comm._xmpp.plugin["xep_0060"].create_node
        safe_send.assert_awaited_once_with(create_node, comm._pubsub_service, node)

    @pytest.mark.asyncio
    async def test_swallows_iq_error_from_create(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        node = "pyobs:event:camera:LogEvent:1"
        with patch.object(comm, "_safe_send", AsyncMock(side_effect=_fake_iq_error())):
            await comm._create_node(node)  # must not raise

    @pytest.mark.asyncio
    async def test_swallows_iq_timeout_from_create(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        node = "pyobs:event:camera:LogEvent:1"
        with patch.object(comm, "_safe_send", AsyncMock(side_effect=slixmpp.exceptions.IqTimeout(iq=None))):
            await comm._create_node(node)  # must not raise

    @pytest.mark.asyncio
    async def test_propagates_unexpected_exceptions_from_create(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        node = "pyobs:event:camera:LogEvent:1"
        with patch.object(comm, "_safe_send", AsyncMock(side_effect=RuntimeError("boom"))):
            with pytest.raises(RuntimeError):
                await comm._create_node(node)


class TestRegisterEventsPreCreation:
    """_register_events' send-only-declaration (handler=None) branch pre-creates the module's
    own event node; the has-a-handler (subscriber) branch never does."""

    def _create_node_calls(self, safe_send: AsyncMock, comm: XmppComm) -> list[Any]:
        assert comm._xmpp is not None
        create_node = comm._xmpp.plugin["xep_0060"].create_node
        return [c for c in safe_send.call_args_list if c.args and c.args[0] is create_node]

    @pytest.mark.asyncio
    async def test_handler_none_with_module_precreates_node(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        comm._module = SimpleNamespace(name="camera")  # type: ignore[assignment]
        safe_send = AsyncMock(return_value=None)
        with patch.object(comm, "_safe_send", safe_send):
            await comm._register_events([LogEvent], handler=None)
        calls = self._create_node_calls(safe_send, comm)
        assert len(calls) == 1
        assert calls[0].args[1:] == (comm._pubsub_service, XmppComm._event_node("camera", LogEvent))

    @pytest.mark.asyncio
    async def test_handler_none_without_module_does_not_precreate(self) -> None:
        """Module-less comms (GUI, admin tools) only subscribe -- out of scope for pre-creation."""
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        comm._module = None
        safe_send = AsyncMock(return_value=None)
        with patch.object(comm, "_safe_send", safe_send):
            await comm._register_events([LogEvent], handler=None)
        assert self._create_node_calls(safe_send, comm) == []

    @pytest.mark.asyncio
    async def test_with_handler_does_not_precreate(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        comm._module = SimpleNamespace(name="camera")  # type: ignore[assignment]
        safe_send = AsyncMock(return_value=None)

        def handler(event: object, sender: str) -> None:
            return None

        with patch.object(comm, "_safe_send", safe_send):
            await comm._register_events([LogEvent], handler=handler)  # type: ignore[arg-type]
        assert self._create_node_calls(safe_send, comm) == []


class TestSubscribeEventWithRetryAbnormalExit:
    """#824: an unexpected failure inside the retry loop must not leave the (peer, event) key
    stuck in _event_subscriptions -- that permanently short-circuits future subscribe attempts
    for that pair (see the `if key in self._event_subscriptions: return` guard) while nothing
    is actually subscribed and nothing is retrying."""

    @pytest.mark.asyncio
    async def test_discards_key_and_reraises_on_unexpected_exception(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        key = ("camera", LogEvent)
        with patch.object(comm, "_safe_send", AsyncMock(side_effect=RuntimeError("boom"))):
            with pytest.raises(RuntimeError):
                await comm._subscribe_event_with_retry("camera", LogEvent)
        assert key not in comm._event_subscriptions

    @pytest.mark.asyncio
    async def test_expected_errors_keep_retrying_key_present(self) -> None:
        """Sanity check that the fix doesn't disturb the existing IqError/IqTimeout retry
        path: those must still be retried, not treated as the new unexpected-exception case."""
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        key = ("camera", LogEvent)

        call_count = 0

        async def flaky_subscribe(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise _fake_iq_error()
            comm._event_subscriptions.discard(key)  # let the while loop exit after success

        with (
            patch.object(comm, "_safe_send", AsyncMock(side_effect=flaky_subscribe)),
            patch("pyobs.comm.xmpp.xmppcomm._retry_delay", return_value=0.0),
            patch("asyncio.sleep", AsyncMock(return_value=None)),
        ):
            await comm._subscribe_event_with_retry("camera", LogEvent)
        assert call_count == 3


class TestSubscribeWithRetryAbnormalExit:
    """Same stuck-state class of bug on the state path (kept in scope: only state node
    *pre-creation* was dropped, retry hardening still applies to state)."""

    @pytest.mark.asyncio
    async def test_removes_state_node_handler_and_reraises_on_unexpected_exception(self) -> None:
        comm = _make_comm()
        comm._xmpp = _make_fake_xmpp()
        node = XmppComm._state_node("camera", ICooling)
        comm._state_node_handlers = {node: (ICooling, [MagicMock()])}
        with patch.object(comm, "_safe_send", AsyncMock(side_effect=RuntimeError("boom"))):
            with pytest.raises(RuntimeError):
                await comm._subscribe_with_retry(node, ICooling)
        assert node not in comm._state_node_handlers
