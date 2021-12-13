from __future__ import annotations

import asyncio
import functools
import inspect
import json
import logging
import re
import time
from collections import Coroutine
from typing import Any, Callable, Dict, Type, List, Optional, TYPE_CHECKING

import slixmpp
import slixmpp.exceptions
from slixmpp import ElementBase
from slixmpp.xmlstream import ET
import xml.sax.saxutils

from pyobs.comm import Comm
from pyobs.events import Event, LogEvent, ModuleOpenedEvent, ModuleClosedEvent
from pyobs.events.event import EventFactory
from pyobs.interfaces import Interface
from pyobs.utils.parallel import Future
from .rpc import RPC
from .xmppclient import XmppClient
if TYPE_CHECKING:
    from pyobs.modules import Module

log = logging.getLogger(__name__)


class EventStanza(ElementBase):  # type: ignore
    name = 'event'
    namespace = 'pyobs:event'


class XmppComm(Comm):
    """A Comm class using XMPP.

    This Comm class uses an XMPP server (e.g. `ejabberd <https://www.ejabberd.im>`_) for communication between modules.
    Essentially required for a connection to the server is a JID, a JabberID. It can be specified in the configuration
    like this::

        comm:
            class: pyobs.xmpp.XmppComm
            jid:  someuser@example.com/pyobs

    Using this, *pyobs* tries to connect to example.com as user ``someuser`` with resource ``pyobs``. Since ``pyobs``
    is the default resource, it can be omitted::

        jid:  someuser@example.com

    Alternatively, one can split the user, domain, and resource (if required) into three different parameters::

        user: someuser
        domain: example.com

    This comes in handy, if one wants to put the basic Comm configuration into a separate file. Imagine a ``_comm.yaml``
    in the same directory as the module config::

        comm_cfg: &comm
            class: pyobs.comm.xmpp.XmppComm
            domain: example.com

    Now in the module configuration, one can simply do this::

        {include _comm.yaml}

        comm:
            <<: *comm
            user: someuser
            password: supersecret

    This allows for a super easy change of the domain for all configurations, which especially makes developing on
    different machines a lot easier.

    The ``server`` parameter can be used, when the server's hostname is different from the XMPP domain. This might,
    e.g., be the case, when connecting to a server via SSH port forwarding::

        jid:  someuser@example.com/pyobs
        server: localhost:52222

    Finally, always make sure that ``use_tls`` is set according to the server's settings, i.e. if it uses TLS, this
    parameter must be True, and False otherwise. Cryptic error messages will follow, if one does not set this properly.

    """
    __module__ = 'pyobs.comm.xmpp'

    def __init__(self, jid: Optional[str] = None, user: Optional[str] = None, domain: Optional[str] = None,
                 resource: str = 'pyobs', password: str = '', server: Optional[str] = None,
                 use_tls: bool = False, *args: Any, **kwargs: Any):
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
        self._rpc: Optional[RPC] = None
        self._connected = False
        self._event_handlers: Dict[Type[Event], List[Callable[[Event, str], Coroutine[[], bool]]]] = {}
        self._online_clients: List[str] = []
        self._interface_cache: Dict[str, List[Type[Interface]]] = {}
        self._user = user
        self._domain = domain
        self._resource = resource
        self._server = server
        self._use_tls = use_tls
        self._loop = asyncio.get_event_loop()

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
        #self._xmpp = slixmpp.ClientXMPP(self._jid, password)
        self._xmpp.add_event_handler('pubsub_publish', self._handle_event)
        self._xmpp.add_event_handler("got_online", self._got_online)
        self._xmpp.add_event_handler("got_offline", self._got_offline)

    def _set_module(self, module: 'Module') -> None:
        """Called, when the module connected to this Comm changes.

        Args:
            module: The module.
        """

        # add features
        if module is not None:
            for i in module.interfaces:
                self._xmpp['xep_0030'].add_feature('pyobs:interface:%s' % i.__name__)

        # update RPC
        if self._rpc is None:
            raise ValueError('No RPC.')
        self._rpc.set_handler(module)

    async def open(self) -> None:
        """Open the connection to the XMPP server.

        Returns:
            Whether opening was successful.
        """

        # create RPC handler
        self._rpc = RPC(self._xmpp, self.module)

        # server given?
        server = () if self._server is None else tuple(self._server.split(':'))

        # prepare session start callback
        connected_event = asyncio.Event()
        self._xmpp.add_event_handler('session_start', lambda _: connected_event.set())

        # connect
        self._xmpp.connect(address=server, force_starttls=self._use_tls, disable_starttls=not self._use_tls)
        self._xmpp.init_plugins()

        # wait for connected
        await connected_event.wait()

        # subscribe to events
        await self.register_event(LogEvent)

        # open Comm
        await Comm.open(self)

        # wait a little and finished
        await asyncio.sleep(1)
        self._connected = True

    async def close(self) -> None:
        """Close connection."""

        # close parent class
        await Comm.close(self)

        # disconnect from xmpp server
        await self._xmpp.disconnect()

    @property
    def name(self) -> Optional[str]:
        """Name of this client."""
        return self._user

    def _failed_auth(self, event: Any) -> None:
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

    async def get_interfaces(self, client: str) -> List[Type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """

        # full JID given?
        if '@' not in client:
            client = '%s@%s/%s' % (client, self._domain, self._resource)

        # does it exist?
        if client not in self._interface_cache:
            # get it
            interface_names = await self._get_interfaces(client)
            self._interface_cache[client] = self._interface_names_to_classes(interface_names)

        # convert to classes
        return self._interface_cache[client]

    async def _get_interfaces(self, jid: str) -> List[str]:
        """Return list of interfaces for the given JID.

        Args:
            jid: JID to get interfaces for.

        Returns:
            List of interface names

        Raises:
            IndexError: If client cannot be found.
        """

        # request features
        try:
            info = await self._xmpp['xep_0030'].get_info(jid=jid, cached=False)
        except slixmpp.exceptions.IqError:
            raise IndexError()

        # extract pyobs interfaces
        if info is None:
            return []
        try:
            if isinstance(info, slixmpp.stanza.iq.Iq):
                info = info['disco_info']
            prefix = 'pyobs:interface:'
            return [i[len(prefix):] for i in info['features'] if i.startswith(prefix)]
        except TypeError:
            raise IndexError()

    async def _supports_interface(self, client: str, interface: Type[Interface]) -> bool:
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
        interfaces = await self.get_interfaces(client)

        # supported?
        return interface in interfaces

    def execute(self, client: str, method: str, signature: inspect.Signature, *args: Any) -> Future:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            signature: Method signature.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        if self._rpc is None:
            raise ValueError('No RPC.')
        return self._rpc.call(self._get_full_client_name(client), method, signature, *args)

    async def _got_online(self, msg: Any) -> None:
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

        # interfaces, first wait a little for the client to connect properly
        await asyncio.sleep(2)
        await self.get_interfaces(jid)

        # send event
        self._send_event_to_module(ModuleOpenedEvent(), msg['from'].username)

    def _got_offline(self, msg: Any) -> None:
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
    def clients(self) -> List[str]:
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

    async def send_event(self, event: Event) -> None:
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

        # send it
        await self._xmpp['xep_0163'].publish(stanza, node='pyobs:event:%s' % event.__class__.__name__,
                                             callback=functools.partial(self._send_event_callback, event=event))

    @staticmethod
    def _send_event_callback(iq: Any, event: Optional[Event] = None) -> None:
        """Called when an event has been successfully sent.

        Args:
            iq: Response package.
            event: Sent event.
        """
        log.debug('%s successfully sent.', event.__class__.__name__)

    async def register_event(self, event_class: Type[Event], handler: Optional[Callable[[Event, str], bool]] = None) \
            -> None:
        """Register an event type. If a handler is given, we also receive those events, otherwise we just
        send them.

        Args:
            event_class: Class of event to register.
            handler: Event handler method.
        """

        # we also want to register all events derived from the given one
        event_classes = self._get_derived_events(event_class)

        # do we have a handler?
        if handler:
            # loop classes
            for ev in event_classes:
                # initialize list
                if ev not in self._event_handlers:
                    self._event_handlers[ev] = []
                # avoid duplicates
                if handler not in self._event_handlers[ev]:
                    # add handler
                    self._event_handlers[ev].append(handler)

        # if event is not a local one, we also need to do some XMPP stuff
        if not event_class.local:
            await self._register_events(event_classes, handler)

    def _get_derived_events(self, event: Type[Event]) -> List[Type[Event]]:
        """Return list of given event itself and all events derived from it.

        Args:
            event: Event class to check.

        Returns:
            List of event classes.
        """
        import pyobs.events
        event_classes: List[Type[Event]] = []
        for cls in inspect.getmembers(pyobs.events, inspect.isclass):
            if issubclass(cls[1], event):
                event_classes.append(cls[1])
        return event_classes

    async def _register_events(self, events: List[Type[Event]],
                               handler: Optional[Callable[[Event, str], bool]] = None) -> None:
        # loop events
        for ev in events:
            # register event at XMPP
            self._xmpp['xep_0030'].add_feature('pyobs:event:%s' % ev.__name__)

            # if we have a handler, we're also interested in receiving such events
            if handler:
                # add interest
                self._xmpp['xep_0163'].add_interest('pyobs:event:%s' % ev.__name__)

        # update caps and send presence
        await self._xmpp['xep_0115'].update_caps()
        self._xmpp.send_presence()

    async def _handle_event(self, msg: Any) -> None:
        """Handles an event.

        Args:
            msg: Received XMPP message.
        """

        # get body, unescape it, parse it
        # node = msg['pubsub_event'][items']['node']
        body = json.loads(xml.sax.saxutils.unescape(msg['pubsub_event']['items']['item']['payload'].text))

        # do we have a <delay> element?
        delay = msg.xml.findall('{urn:xmpp:delay}delay')
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

    def _send_event_to_module(self, event: Event, from_client: str) -> None:
        """Send an event to all connected modules.

        Args:
            event: Event to send.
            from_client: Client that sent the event.
        """

        # send it
        if event.__class__ in self._event_handlers:
            for handler in self._event_handlers[event.__class__]:
                # handle it
                ret = handler(event, from_client)
                if asyncio.iscoroutine(ret):
                    asyncio.create_task(ret)


__all__ = ['XmppComm']
