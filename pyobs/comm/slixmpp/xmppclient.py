import asyncio
import logging
import threading
import slixmpp
import slixmpp.xmlstream
from typing import List, Any

from pyobs.comm.slixmpp.xep_0009.rpc import XEP_0009
from pyobs.comm.slixmpp.xep_0009_timeout import XEP_0009_timeout


log = logging.getLogger(__name__)


class XmppClient(slixmpp.ClientXMPP):  # type: ignore
    """XMPP client for pyobs."""

    def __init__(self, jid: str, password: str):
        """Create a new XMPP client.

        An XmppClient handles the actual XMPP communication for the XmppComm module.

        Args:
            jid: Connect to the XMPP server with the given JID.
            password: Password to use for connection.
        """

        slixmpp.ClientXMPP.__init__(self, jid, password)

        # stuff
        self._connect_event = threading.Event()
        self._logs_node = 'logs'
        self._auth_event = threading.Event()
        self._auth_success = False

        # auto-accept invitations
        self.auto_authorize = True

        # register plugins
        self.register_plugin('xep_0009', module=XEP_0009)  # RPC
        self.register_plugin('xep_0009_timeout', module=XEP_0009_timeout)  # RPC timeout
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0060')  # PubSub
        self.register_plugin('xep_0115')  # Entity Capabilities
        self.register_plugin('xep_0163')  # Personal Eventing Protocol
        self.register_plugin('xep_0199')  # XMPP Ping

        # enable keep alive pings
        self['xep_0199'].enable_keepalive(300, 30)

        # handle session_start and message events
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler('auth_success', lambda ev: self._auth(True))
        self.add_event_handler('failed_auth', lambda ev: self._auth(False))

    def wait_connect(self) -> bool:
        """Wait for client to connect.

        Returns:
            Success or not.
        """

        # wait for auth and check
        self._auth_event.wait()
        if not self._auth_success:
            log.error('Invalid credentials for connecting to XMPP server.')
            return False

        # wait for final connect
        self._connect_event.wait()

        # connected
        return True

    def session_start(self, event: Any) -> None:
        """Session start event.

        Args:
            event: The event sent at session start.
        """
        log.info('Connected to server.')

        # send presence and get roster
        self.send_presence()
        self.get_roster()

        # send connected event
        self._connect_event.set()

    def _auth(self, success: bool) -> None:
        """Called after authentification.

        Args:
            success: Whether or not the authentification was successful.
        """
        # store and fire
        self._auth_success = success
        self._auth_event.set()


__all__ = ['XmppClient']
