"""JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid() helper --
pure/synchronous, no network involved, so these run as plain unit tests."""

from __future__ import annotations

import pytest

from pyobs.comm.xmpp import XmppComm, is_valid_jid


class TestIsValidJid:
    def test_accepts_bare_jid(self) -> None:
        assert is_valid_jid("user@example.com") is True

    def test_accepts_jid_with_resource(self) -> None:
        assert is_valid_jid("user@example.com/pyobs") is True

    def test_rejects_trailing_slash_with_no_resource(self) -> None:
        """The actual production bug this was found from: a JID ending in "/" with nothing
        after it -- e.g. saved from an account entry someone typed a trailing slash into."""
        assert is_valid_jid("admin@monet.saao.ac.za/") is False

    def test_rejects_missing_at_sign(self) -> None:
        assert is_valid_jid("notanemail") is False

    def test_rejects_trailing_garbage_after_resource(self) -> None:
        """re.match alone doesn't anchor the end -- confirms the pattern is anchored so this
        doesn't silently pass as a valid prefix."""
        assert is_valid_jid("user@example.com/resource/extra") is False

    def test_rejects_empty_string(self) -> None:
        assert is_valid_jid("") is False


class TestXmppCommJidConstruction:
    """async def, not plain def -- XmppComm.__init__ calls asyncio.get_event_loop(), which
    needs a running loop to behave consistently across the full suite (matches the
    convention already used by test_safe_send.py etc. for anything constructing XmppComm)."""

    @pytest.mark.asyncio
    async def test_accepts_bare_jid_and_attaches_default_resource(self) -> None:
        comm = XmppComm(jid="user@example.com")
        assert comm._user == "user"
        assert comm._domain == "example.com"
        assert comm._resource == "pyobs"
        assert comm._jid == "user@example.com/pyobs"

    @pytest.mark.asyncio
    async def test_accepts_jid_with_explicit_resource(self) -> None:
        comm = XmppComm(jid="user@example.com/myresource")
        assert comm._resource == "myresource"

    @pytest.mark.asyncio
    async def test_raises_with_descriptive_message_on_trailing_slash(self) -> None:
        with pytest.raises(ValueError, match="admin@monet.saao.ac.za/"):
            XmppComm(jid="admin@monet.saao.ac.za/")

    @pytest.mark.asyncio
    async def test_raises_on_malformed_jid(self) -> None:
        with pytest.raises(ValueError, match="Invalid JID format"):
            XmppComm(jid="notanemail")
