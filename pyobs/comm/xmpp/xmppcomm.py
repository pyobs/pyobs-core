import json
import logging
import re
import threading
import time
from typing import Any
from sleekxmpp import ElementBase
from sleekxmpp.xmlstream import ET
import xml.sax.saxutils

from pyobs.comm import Comm
from pyobs.events import Event, LogEvent, ModuleOpenedEvent, ModuleClosedEvent
from pyobs.events.event import EventFactory
from .rpc import RPC
from .xmppclient import XmppClient

log = logging.getLogger(__name__)


class EventStanza(ElementBase):
    name = 'event'
    namespace = 'pyobs:event'


class XmppComm(Comm):
    """Comm module for XMPP."""

    def __init__(self, jid: str = None, user: str = None, domain: str = None, resource: str = 'pyobs',
                 password: str = None, server: str = None, use_tls: bool = False, *args, **kwargs):
        """Create a new XMPP Comm module.

        Either a fill JID needs to be provided, or a set of user/domian/resource, from which a JID is built.

        Args:
            jid: JID to connect as.
            user: Username part of the JID.
            domain: Domain part of the JID.
            resource: Resource part of the JID.
            password: Password for given JID.
            server: Server to connect to. If not given, domain from JID is used.
            use_tls: Whether or not to use TLS.
        """
        Comm.__init__(self, *args, **kwargs)

        # variables
        self._rpc = None
        self._connected = False
        self._command_handlers = {}
        self._event_handlers = {}
        self._online_clients = []
        self._interface_cache = {}
        self._user = user
        self._domain = domain
        self._resource = resource
        self._server = server
        self._use_tls = use_tls

        # build jid
        if jid:
            # resource given in jid?
            if '/' not in jid:
                jid += '/' + resource

            # get user/domain/resource and write it back to config
            m = re.match(r'([\w_\-\.]+)@([\w_\-\.]+)\/([\w_\-\.]+)', jid)
            if not m:
                log.error('Invalid JID format.')
                raise ValueError()
            self._user = m.group(1)
            self._domain = m.group(2)
            self._resource = m.group(3)

            # set jid itself
            self._jid = jid

        else:
            self._jid = '%s@%s/%s' % (self._user, self._domain, self._resource)

        # create client
        self._xmpp = XmppClient(self._jid, password)
        self._xmpp.add_event_handler('message', self._handle_message)
        self._xmpp.add_event_handler('pubsub_publish', self._handle_event)
        self._xmpp.add_event_handler("got_online", self._got_online)
        self._xmpp.add_event_handler("got_offline", self._got_offline)

    def _set_module(self, module):
        """Called, when the module connected to this Comm changes.

        Args:
            module: The module.
        """

        # add features
        if module:
            for i in module.interfaces:
                self._xmpp['xep_0030'].add_feature('pyobs:interface:%s' % i.__name__)

        # update RPC
        self._rpc.set_handler(module)

    def open(self) -> bool:
        """Open the connection to the XMPP server.

        Returns:
            Whether opening was successful.
        """
        Comm.open(self)

        # create RPC handler
        self._rpc = RPC(self._xmpp, self.module)

        # server given?
        server = () if self._server is None else tuple(self._server.split(':'))

        # connect
        if self._xmpp.connect(server, use_tls=self._use_tls, reattempt=False):
            # start processing
            self._xmpp.process(block=False)

            # wait for connected
            if not self._xmpp.wait_connect():
                log.error('Could not connect to XMPP server.')
                return False
            self._connected = True

            # subscribe to events
            self.register_event(LogEvent)

            # success
            return True

        else:
            # TODO: catch exceptions in open() methods
            log.error('Could not connect to server.')
            return False

    def close(self):
        """Close connection."""

        # close parent class
        Comm.close(self)

        # disconnect from xmpp server
        self._xmpp.disconnect()

    @property
    def name(self) -> str:
        """Name of this client."""
        return self._user

    def _failed_auth(self, event):
        """Authentification failed.

        Args:
            event: XMPP event.
        """
        print('Authorization at server failed.')

    def _get_full_client_name(self, name: str) -> str:
        """Builds full JID from a given username.

        Args:
            name: Username to build JID for.

        Returns:
            Full JID for given user.
        """
        return name if '@' in name else '%s@%s/%s' % (name, self._domain, self._resource)

    def get_interfaces(self, client: str) -> list:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError, if client cannot be found.
        """

        # full JID given?
        if '@' not in client:
            client = '%s@%s/%s' % (client, self._domain, self._resource)

        # get interfaces
        if client not in self._interface_cache:
            # get interface names
            interface_names = self._xmpp.get_interfaces(client)

            # get interfaces
            self._interface_cache[client] = self._interface_names_to_classes(interface_names)

        # convert to classes
        return self._interface_cache[client]

    def _supports_interface(self, client: str, interface) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether or not interface is supported.
        """

        # full JID given?
        if '@' not in client:
            client = '%s@%s/%s' % (client, self._domain, self._resource)

        # update interface cache and get interface names
        interfaces = self.get_interfaces(client)

        # supported?
        return interface in interfaces

    def execute(self, client: str, method: str, *args) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        return self._rpc.call(self._get_full_client_name(client), method, *args)

    def _got_online(self, msg):
        """If a new client connects, add it to list.

        Args:
            msg: XMPP message.
        """

        # append to list
        jid = msg['from'].full
        if jid not in self._online_clients:
            self._online_clients.append(jid)

        # clear interface cache, just in case there is something there
        if jid in self._interface_cache:
            del self._interface_cache[jid]

        # send event
        self._send_event_to_module(ModuleOpenedEvent(), msg['from'].username)

    def _got_offline(self, msg):
        """If a new client disconnects, remove it from list.

        Args:
            msg: XMPP message.
        """

        # remove from list
        jid = msg['from'].full
        self._online_clients.remove(jid)

        # clear interface cache
        if jid in self._interface_cache:
            del self._interface_cache[jid]

        # send event
        self._send_event_to_module(ModuleClosedEvent(), msg['from'].username)

    @property
    def clients(self):
        """Returns list of currently connected clients.

        Returns:
            (list) List of currently connected clients.
        """
        return [c[:c.find('@')] for c in self._online_clients]

    @property
    def client(self) -> XmppClient:
        """Returns the XMPP client.

        Returns:
            The XMPP client.
        """
        return self._xmpp

    def _handle_message(self, msg):
        """Handle a new incoming XMPP message.

        Args:
            msg: Received XMPP message.
        """

        cmd = msg['body']
        if cmd in self._command_handlers:
            for handler in self._command_handlers[cmd]:
                # create thread and start it
                thread = threading.Thread(name="cmd_%s" % handler.__name__,
                                          target=handler, args=(msg['from'], cmd),
                                          daemon=True)
                thread.start()

    def add_command_handler(self, command: str, handler):
        """Add a command handler.

        Args:
            command (str): Name of command to handle.
            handler: Method that handles the command
        """
        if command not in self._command_handlers:
            self._command_handlers[command] = []
        self._command_handlers[command].append(handler)

    def del_command_handler(self, command: str, handler):
        """Delete a command handler.

        Args:
            command: Name of command to handle.
            handler: Method that handles the command
        """
        if command not in self._command_handlers:
            return
        self._command_handlers[command].remove(handler)

    def send_text_message(self, client: str, msg: str):
        """Send a text message to another client.

        Args:
            client: ID of client to send message to.
            msg: Message to send.
        """
        self._xmpp.send_message(client, msg)

    def send_event(self, event: Event):
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """

        # create stanza
        stanza = EventStanza()

        # dump event to JSON and escape it
        body = xml.sax.saxutils.escape(json.dumps(event.to_json()))

        # set xml and send event
        stanza.xml = ET.fromstring('<event xmlns="pyobs:event">%s</event>' % body)
        self._xmpp['xep_0163'].publish(stanza, node='pyobs:event:%s' % event.__class__.__name__)

    def register_event(self, event_class, handler=None):
        """Register an event type. If a handler is given, we also receive those events, otherwise we just
        send them.

        Args:
            event_class: Class of event to register.
            handler: Event handler method.
        """

        # do we have a handler?
        if handler:
            # store handler
            if event_class not in self._event_handlers:
                self._event_handlers[event_class] = []
            self._event_handlers[event_class].append(handler)

        # if event is not a local one, we also need to do some XMPP stuff
        if not event_class.local:
            # register event at XMPP
            self._xmpp['xep_0030'].add_feature('pyobs:event:%s' % event_class.__name__)

            # if we have a handler, we're also interested in receiving such events
            if handler:
                # add interest
                self._xmpp['xep_0163'].add_interest('pyobs:event:%s' % event_class.__name__)

            # update caps and send presence
            self._xmpp['xep_0115'].update_caps()
            self._xmpp.send_presence()

    def _handle_event(self, msg):
        """Handles an event.

        Args:
            msg: Received XMPP message.
        """

        # get body, unescape it, parse it
        # node = msg['pubsub_event'][items']['node']
        body = json.loads(xml.sax.saxutils.unescape(msg['pubsub_event']['items']['item']['payload'].text))

        # do we have a <delay> element?
        delay = msg.findall('{urn:xmpp:delay}delay')
        if len(delay) > 0:
            # ignore this message
            return

        # did we send this?
        if msg['from'] == self._xmpp.boundjid.bare:
            return

        # create event and check timestamp
        event = EventFactory.from_dict(body)
        if event is None:
            return
        if time.time() - event.timestamp > 30:
            # event is more than 30 seconds old, ignore it
            # we do this do avoid resent events after a reconnect
            return

        # send it to module
        self._send_event_to_module(event, msg['from'].username)

    def _send_event_to_module(self, event: Event, from_client: str):
        """Send an event to all connected modules.

        Args:
            event: Event to send.
            from_client: Client that sent the event.
        """

        # send it
        if event.__class__ in self._event_handlers:
            for handler in self._event_handlers[event.__class__]:
                # create thread and start it
                thread = threading.Thread(name="event_%s" % handler.__name__,
                                          target=handler, args=(event, from_client),
                                          daemon=True)
                thread.start()


__all__ = ['XmppComm']
