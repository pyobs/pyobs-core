import asyncio
import logging
from typing import Any

import slixmpp
import slixmpp.xmlstream
from slixmpp.xmlstream import StanzaBase

from pyobs.comm.xmpp.xep_0009.rpc import XEP_0009
from pyobs.comm.xmpp.xep_0009_timeout import XEP_0009_timeout

log = logging.getLogger(__name__)


class XmppClient(slixmpp.ClientXMPP):
    """XMPP client for pyobs."""

    def __init__(self, jid: str, password: str, **kwargs: Any):
        """Create a new XMPP client.

        An XmppClient handles the actual XMPP communication for the XmppComm module.

        Args:
            jid: Connect to the XMPP server with the given JID.
            password: Password to use for connection.
        """

        slixmpp.ClientXMPP.__init__(self, jid, password, **kwargs)

        # stuff
        self._connect_event = asyncio.Event()
        self._auth_event = asyncio.Event()
        self._auth_success = False
        self._jid_conflict = False
        self._conflict_reason: str | None = None

        # auto-accept invitations
        self.auto_authorize = True

        # register plugins
        self.register_plugin("xep_0009", module=XEP_0009)  # RPC
        self.register_plugin("xep_0009_timeout", module=XEP_0009_timeout)  # RPC timeout
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0045")  # Multi-User Chat
        self.register_plugin("xep_0060")  # PubSub
        self.register_plugin("xep_0115")  # Entity Capabilities
        self.register_plugin("xep_0163")  # Personal Eventing Protocol
        self.register_plugin("xep_0199")  # XMPP Ping

        # enable keep alive pings
        self["xep_0199"].enable_keepalive()

        # handle session_start and message events
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("auth_success", lambda ev: self._auth(True))
        self.add_event_handler("failed_auth", lambda ev: self._auth(False))
        self.add_event_handler("failed_all_auth", self.failed_all_auth)
        self.add_event_handler("stream_error", self._stream_error)
        self.add_filter("in", self._filter_messages)

    def reconnect(self, wait: int | float = 2.0, reason: str = "Reconnecting") -> Any:
        """Disconnect only, instead of slixmpp's default reconnect-in-place.

        xep_0199's keepalive calls this on ping timeout. slixmpp's own
        implementation would reconnect this same client object, while
        XmppComm's "disconnected" handler independently spins up a brand-new
        XmppClient. The two then fight over the same JID resource, each
        kicking the other off the server ("replaced by new connection"),
        forever. Leaving reconnection solely to XmppComm avoids that.
        """
        return self.disconnect(0.0, reason=reason)

    def _filter_messages(self, stanza: StanzaBase) -> StanzaBase | None:
        # if a user with same JID is already connected, we get a conflict
        if '<conflict xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />' in str(stanza):
            self._jid_conflict = True
            return None
        return stanza

    def _stream_error(self, error: Any) -> None:
        """Called when the server sends a <stream:error/>, e.g. when this connection gets
        kicked because another session took over the same JID/resource.

        Args:
            error: The stream error stanza.
        """
        if error["condition"] == "conflict":
            self._jid_conflict = True
            self._conflict_reason = error["text"] or None

    @property
    def kicked_by_conflict(self) -> bool:
        """Whether this client was (or is being) kicked because another session connected
        with the same JID, rather than disconnecting for some other reason."""
        return self._jid_conflict

    @property
    def conflict_reason(self) -> str | None:
        """Human-readable reason text sent alongside the conflict stream error, if any."""
        return self._conflict_reason

    async def wait_connect(self) -> bool:
        """Wait for client to connect.

        Returns:
            Success or not.
        """

        # wait for auth and check
        await self._auth_event.wait()
        if not self._auth_success:
            log.error("Invalid credentials for connecting to XMPP server.")
            return False

        # wait for final connect
        while not self._connect_event.is_set():
            if self._jid_conflict:
                log.error("Another user is already connected with the same JID.")
                return False
            await asyncio.sleep(0.1)

        # connected
        return True

    async def session_start(self, event: Any) -> None:
        """Session start event.

        Args:
            event: The event sent at session start.
        """
        log.info("Connected to server.")

        # send presence and get roster
        self.send_presence()
        await self.get_roster()

        # send connected event
        self._connect_event.set()

    def _auth(self, success: bool) -> None:
        """Called after authentication.

        Args:
            success: Whether the authentication was successful.
        """
        # store and fire
        if success:
            self._auth_success = True
            self._auth_event.set()

    def failed_all_auth(self, event: Any) -> None:
        log.error("All authentication attempts failed.")
        self._auth_success = False
        self._auth_event.set()


__all__ = ["XmppClient"]
