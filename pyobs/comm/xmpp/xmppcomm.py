from __future__ import annotations

import asyncio
import dataclasses
import functools
import json
import logging
import re
import ssl
import time
import xml.sax.saxutils
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin, get_type_hints

import slixmpp
import slixmpp.exceptions
from slixmpp import ElementBase
from slixmpp.xmlstream import ET
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXMLMask

from pyobs.comm import Comm
from pyobs.events import Event, LogEvent, ModuleClosedEvent, ModuleOpenedEvent
from pyobs.events.event import EventFactory
from pyobs.interfaces import Interface
from pyobs.utils import exceptions as exc

from .rpc import RPC
from .xmppclient import XmppClient

if TYPE_CHECKING:
    from pyobs.modules import Module

log = logging.getLogger(__name__)


class EventStanza(ElementBase):
    name = "event"
    namespace = "pyobs:event"


class StateStanza(ElementBase):
    name = "state"
    namespace = "pyobs:state"


class XmppComm(Comm):
    """A Comm class using XMPP.

    This Comm class uses an XMPP server (e.g. `ejabberd <https://www.ejabberd.im>`_) for communication between modules.
    Essentially required for a connection to the server is a JID, a JabberID. It can be specified in the configuration
    like this::

        comm:
            class: pyobs.comm.xmpp.XmppComm
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
            class: pyobs.comm.sleekxmpp.XmppComm
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

    __module__ = "pyobs.comm.xmpp"

    def __init__(
        self,
        jid: str | None = None,
        user: str | None = None,
        domain: str | None = None,
        resource: str = "pyobs",
        password: str = "",
        server: str | None = None,
        use_tls: bool = False,
        ignore_cert_errors: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        """Create a new XMPP Comm module.

        Either a fill JID needs to be provided, or a set of user/domian/resource, from which a JID is built.

        Args:
            jid: JID to connect as.
            user: Username part of the JID.
            domain: Domain part of the JID.
            resource: Resource part of the JID.
            password: Password for given JID.
            server: Server to connect to. If not given, domain from JID is used.
            use_tls: Whether to use TLS.
        """
        Comm.__init__(self, *args, **kwargs)

        # variables
        self._connected = False
        self._online_clients: list[str] = []
        self._interface_cache: dict[str, asyncio.Future[list[type[Interface]]]] = {}
        self._user = user
        self._password = password
        self._domain = domain
        self._resource = resource
        self._server = server
        self._use_tls = use_tls
        self._ignore_cert_errors = ignore_cert_errors
        self._loop = asyncio.get_event_loop()
        self._safe_send_attempts = 5
        self._safe_send_wait = 1

        # build jid
        if jid:
            # resource given in jid?
            if "/" not in jid:
                jid += "/" + resource

            # get user/domain/resource and write it back to config
            m = re.match(r"([\w_\-\.]+)@([\w_\-\.]+)\/([\w_\-\.]+)", jid)
            if not m:
                log.error("Invalid JID format.")
                raise ValueError()
            self._user = m.group(1)
            self._domain = m.group(2)
            self._resource = m.group(3)

            # set jid itself
            self._jid = jid

        else:
            self._jid = f"{self._user}@{self._domain}/{self._resource}"

        #  client and RPC handler
        self._xmpp: XmppClient | None = None
        self._rpc: RPC | None = None

        # pubsub for states
        self._pubsub_service = f"pubsub.{self._domain}"
        self._state_node_handlers: dict[str, tuple[type[Interface], list[Callable[[Any], None]]]] = {}

    def _set_module(self, module: Module) -> None:
        """Called, when the module connected to this Comm changes.

        Args:
            module: The module.
        """
        self._module = module

    async def open(self) -> None:
        """Open the connection to the XMPP server.

        Returns:
            Whether opening was successful.
        """

        # connect
        await self._connect()

        # subscribe to events
        await self.register_event(LogEvent)

        # open Comm
        await Comm.open(self)

    async def _connect(self) -> None:
        # create client
        self._xmpp = XmppClient(self._jid, self._password)

        # self._xmpp = slixmpp.ClientXMPP(self._jid, password)
        # Register directly with an XML mask rather than via pubsub_publish.
        # slixmpp's StanzaPath matcher requires plugins to be lazily loaded
        # before matching — for live notifications (not triggered by an IQ)
        # this never happens, so pubsub_publish is never fired. MatchXMLMask
        # works on raw XML and fires reliably for every pubsub notification.
        self._xmpp.register_handler(
            Callback(
                "pyobs pubsub event",
                MatchXMLMask(
                    '<message xmlns="jabber:client">'
                    '<event xmlns="http://jabber.org/protocol/pubsub#event">'
                    "<items /></event></message>"
                ),
                self._handle_event_sync,
            )
        )
        self._xmpp.add_event_handler("got_online", self._got_online)
        self._xmpp.add_event_handler("got_offline", self._got_offline)
        self._xmpp.add_event_handler("disconnected", self._disconnected)

        # server given?
        server: str = "localhost"
        port: int = 5222
        if self._server is not None:
            if ":" in self._server:
                server, sport = self._server.split(":")
                port = int(sport)
            else:
                server, port = self._server, 5222
        elif self._domain is not None:
            server, port = self._domain, 5222

        # add features
        if self._module is not None:
            for i in self._module.interfaces:
                self._xmpp["xep_0030"].add_feature(f"pyobs:interface:{i.__name__}")

        # RPC
        self._rpc = RPC(self, self._xmpp, None)
        self._rpc.set_handler(self._module)

        # connect
        self._xmpp.enable_starttls = self._use_tls
        self._xmpp.enable_direct_tls = self._use_tls
        self._xmpp.enable_plaintext = not self._use_tls
        self._xmpp["feature_mechanisms"].unencrypted_scram = not self._use_tls
        if self._ignore_cert_errors:
            self._xmpp.ssl_context.check_hostname = False
            self._xmpp.ssl_context.verify_mode = ssl.CERT_NONE

        # connect
        await self._xmpp.connect(host=server, port=port)
        self._xmpp.init_plugins()  # type: ignore

        # wait for connected
        if not await self._xmpp.wait_connect():
            if self._module is not None:
                self._module.quit()
            return

        # wait a little and finished
        await asyncio.sleep(1)
        self._connected = True

    async def close(self) -> None:
        """Close connection."""

        # close parent class
        await Comm.close(self)

        # disconnect from sleekxmpp server
        if self._xmpp is not None:
            await self._xmpp.disconnect()

    async def _reconnect(self) -> None:
        """Sleep a little and reconnect"""
        await asyncio.sleep(2)
        await self._connect()

    def _disconnected(self, event: Any) -> None:
        """Reset connection after disconnect."""
        if self._closing.is_set():
            return
        log.info("Disconnected from server, waiting for reconnect...")

        # disconnect all clients
        for jid in self._online_clients:
            self._jid_got_offline(jid)

        # reconnect
        asyncio.create_task(self._reconnect())

    @property
    def name(self) -> str | None:
        """Name of this client."""
        return self._user

    def _failed_auth(self, event: Any) -> None:
        """Authentication failed.

        Args:
            event: XMPP event.
        """
        print("Authorization at server failed.")

    def _get_full_client_name(self, name: str) -> str:
        """Builds full JID from a given username.

        Args:
            name: Username to build JID for.

        Returns:
            Full JID for given user.
        """
        return name if "@" in name else f"{name}@{self._domain}/{self._resource}"

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """

        # full JID given?
        if "@" not in client:
            client = f"{client}@{self._domain}/{self._resource}"

        # return them from cache
        return await self._interface_cache[client]

    async def _get_interfaces(self, jid: str, attempts: int = 3) -> list[str]:
        """Return list of interfaces for the given JID.

        Args:
            jid: JID to get interfaces for.

        Returns:
            List of interface names or empty list, if an error occurred.
        """

        # request features
        try:
            info = await self._safe_send(self.client["xep_0030"].get_info, jid=jid, cached=False)
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            return []

        # extract pyobs interface names
        if info is None:
            return []
        try:
            if isinstance(info, slixmpp.stanza.iq.Iq):
                info = info["disco_info"]
            prefix = "pyobs:interface:"
            interface_names = [i[len(prefix) :] for i in info["features"] if i.startswith(prefix)]
        except TypeError:
            raise IndexError()

        # IModule not in list?
        if "IModule" not in interface_names:
            # try again or quit?
            if attempts == 0:
                return []
            else:
                await asyncio.sleep(5)
                interface_names = await self._get_interfaces(jid, attempts - 1)

        # finished
        return interface_names

    async def _supports_interface(self, client: str, interface: type[Interface]) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether or not interface is supported.
        """

        # full JID given?
        if "@" not in client:
            client = f"{client}@{self._domain}/{self._resource}"

        # update interface cache and get interface names
        interfaces = await self.get_interfaces(client)

        # supported?
        return interface in interfaces

    async def execute(self, client: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            annotation: Method annotation.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """

        # prepare
        if self._rpc is None:
            raise ValueError("No RPC.")
        jid = self._get_full_client_name(client)

        # call
        try:
            return await self._rpc.call(jid, method, annotation, *args)
        except slixmpp.exceptions.IqError:
            raise exc.RemoteError(client, f"Could not call {method} on {client}.")
        except slixmpp.exceptions.IqTimeout:
            raise exc.RemoteTimeoutError(client, f"Call to {method} on {client} timed out.")

    async def _got_online(self, msg: Any) -> None:
        """If a new client connects, add it to list.

        Args:
            msg: XMPP message.
        """

        # get jid, ignore event if it's myself
        jid = msg["from"].full
        if jid == self._jid:
            return

        # clear interface cache, just in case there is something there
        if jid in self._interface_cache:
            del self._interface_cache[jid]

        # create future for interfaces
        self._interface_cache[jid] = asyncio.get_running_loop().create_future()

        # request interfaces
        interface_names = await self._get_interfaces(jid)

        # if no interfaces are implemented (not even IModule), quit here
        if len(interface_names) == 0:
            module = jid[: jid.index("@")]
            log.debug("Module %s does not seem to implement IModule, ignoring.", module)
            return

        # store interfaces — guard against a second _got_online for the same JID
        # (ejabberd may send multiple presence stanzas) racing against the first
        future = self._interface_cache.get(jid)
        if future is not None and not future.done():
            future.set_result(self._interface_names_to_classes(interface_names))

        # append to list
        if jid not in self._online_clients:
            self._online_clients.append(jid)

        # send event
        self._send_event_to_module(ModuleOpenedEvent(), msg["from"].username)

    def _got_offline(self, msg: Any) -> None:
        """If a new client disconnects, remove it from list.

        Args:
            msg: XMPP message.
        """
        self._jid_got_offline(msg["from"].full)

    def _jid_got_offline(self, jid: str) -> None:
        """If a new client disconnects, remove it from list.

        Args:
            jid: JID that got offline.
        """

        # remove from list
        if jid in self._online_clients:
            self._online_clients.remove(jid)

        # clear interface cache
        if jid in self._interface_cache:
            del self._interface_cache[jid]

        # send event
        username = jid[: jid.find("@")]
        self._send_event_to_module(ModuleClosedEvent(), username)

    @property
    def clients(self) -> list[str]:
        """Returns list of currently connected clients.

        Returns:
            (list) List of currently connected clients.
        """
        return [c[: c.find("@")] for c in self._online_clients]

    @property
    def client(self) -> XmppClient:
        """Returns the XMPP client.

        Returns:
            The XMPP client.
        """
        if self._xmpp is None:
            raise ValueError("No XMPP client.")
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
        stanza.xml = ET.fromstring(f'<event xmlns="pyobs:event">{body}</event>')

        # send it
        await self._safe_send(
            self.client["xep_0163"].publish,
            stanza,
            node=f"pyobs:event:{event.__class__.__name__}",
            callback=functools.partial(self._send_event_callback, event=event),
        )

        # send it to local module
        if self._module is not None:
            self._send_event_to_module(event, self._module.name)

    @staticmethod
    def _send_event_callback(iq: Any, event: Event | None = None) -> None:
        """Called when an event has been successfully sent.

        Args:
            iq: Response package.
            event: Sent event.
        """
        log.debug("%s successfully sent.", event.__class__.__name__)

    async def _register_events(
        self, events: list[type[Event]], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None:
        # loop events
        for ev in events:
            # register event at XMPP
            self.client["xep_0030"].add_feature(f"pyobs:event:{ev.__name__}")

            # if we have a handler, we're also interested in receiving such events
            if handler:
                # add interest
                self.client["xep_0163"].add_interest(f"pyobs:event:{ev.__name__}")

        # update caps and send presence
        await self._safe_send(self.client["xep_0115"].update_caps)
        self.client.send_presence()

    def _handle_event_sync(self, msg: Any) -> None:
        """Synchronous entry point for the MatchXMLMask Callback.

        Callback handlers must be synchronous; this creates an asyncio task
        so that _handle_event can await safely.
        """
        asyncio.create_task(self._handle_event(msg))

    async def _handle_event(self, msg: Any) -> None:
        """Handles an event.

        Args:
            msg: Received XMPP message.
        """

        node = msg["pubsub_event"]["items"]["node"]

        # State-node notifications: dispatch to handler if registered, then return.
        # map_node_event() cannot be used here because the XEP-0060 plugin iterates
        # Items.iterables (empty) to fire mapped events, so live notifications are
        # silently dropped. _handle_event (pubsub_publish) fires reliably for all nodes.
        if node.startswith("pyobs:state:"):
            if node in self._state_node_handlers:
                if len(msg.xml.findall("{urn:sleekxmpp:delay}delay")) == 0:
                    interface, callbacks = self._state_node_handlers[node]
                    payload = msg["pubsub_event"]["items"]["item"]["payload"]
                    if payload is not None:
                        state_obj = self._xml_to_dataclass(payload, interface.state)
                        for callback in callbacks:
                            callback(state_obj)
                    # If payload is None it's a retract notification for the old
                    # max_items:1 slot — the matching publish notification (with
                    # payload) arrives in the next pubsub_publish event.
            return

        # get body, unescape it, parse it
        # node = msg['pubsub_event'][items']['node']
        body = json.loads(xml.sax.saxutils.unescape(msg["pubsub_event"]["items"]["item"]["payload"].text))

        # do we have a <delay> element?
        delay = msg.xml.findall("{urn:sleekxmpp:delay}delay")
        if len(delay) > 0:
            # ignore this message
            return

        # did we send this?
        if msg["from"] == self.client.boundjid.bare:
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
        self._send_event_to_module(event, msg["from"].username)

    async def _safe_send(self, method: Callable[[Any], Coroutine[Any, Any, None]], *args: Any, **kwargs: Any) -> Any:
        """Safely send an XMPP message.

        Args:
            method: Method to call.
            *args: Parameters for method.
            **kwargs: Parameters for method.        except slixmpp.exceptions.IqError:
            raise RemoteException("Could not send command.")
        except slixmpp.exceptions.IqTimeout:
            raise exc()


        Returns:
            Return value from method.
        """

        # try multiple times
        iq = None
        for i in range(self._safe_send_attempts):
            try:
                # execute method and return result
                return await method(*args, **kwargs)

            except slixmpp.exceptions.IqTimeout as timeout:
                # timeout occurred, try again after some wait
                iq = timeout.iq
                await asyncio.sleep(self._safe_send_wait)

        # never should reach this
        raise slixmpp.exceptions.IqTimeout(iq)  # type: ignore

    def cast_to_simple_pre(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them to be sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """

        if isinstance(value, str):
            return True, xml.sax.saxutils.escape(value)
        else:
            return False, value

    def cast_to_real_post(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them after being sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """

        if isinstance(value, str):
            return True, xml.sax.saxutils.unescape(value)
        else:
            return False, value

    @staticmethod
    def _state_namespace(interface: type[Interface]) -> str:
        return f"urn:pyobs:state:{interface.__name__}:{interface.version}"

    @staticmethod
    def _state_node(module: str, interface: type[Interface]) -> str:
        return f"pyobs:state:{module}:{interface.__name__}:{interface.version}"

    @staticmethod
    def _dataclass_to_xml(state: Any, namespace: str) -> ET.Element:
        root = ET.Element(f"{{{namespace}}}state")
        for f in dataclasses.fields(state):
            value = getattr(state, f.name)
            # Use ET.Element + append (not SubElement) so children stay in the
            # empty namespace and elem.find("fieldname") works on the receiving side.
            child = ET.Element(f.name)
            if isinstance(value, bool):
                child.text = "true" if value else "false"
            elif isinstance(value, StrEnum):
                child.text = value.value
            else:
                child.text = str(value)
            root.append(child)
        return root

    @staticmethod
    def _xml_to_dataclass(elem: ET.Element, state_cls: type) -> Any:
        hints = get_type_hints(state_cls, include_extras=True)
        # Extract namespace from root element tag, e.g. "{urn:pyobs:state:ICooling:1}state"
        # Children may arrive namespaced (after ejabberd round-trip) or plain (locally),
        # so try both forms.
        ns = ""
        if elem.tag.startswith("{"):
            ns = elem.tag[1 : elem.tag.index("}")]
        kwargs = {}
        for f in dataclasses.fields(state_cls):
            # Try namespaced lookup first, then plain
            child = elem.find(f"{{{ns}}}{f.name}") if ns else None
            if child is None:
                child = elem.find(f.name)
            if child is None or child.text is None:
                continue
            field_type = hints[f.name]
            # strip Optional (T | None) to get the concrete type
            args = get_args(field_type)
            if args and type(None) in args:
                field_type = next(a for a in args if a is not type(None))
            # unwrap Annotated[T, ...] → T for type dispatch
            if get_origin(field_type) is Annotated:
                field_type = get_args(field_type)[0]
            if field_type is bool:
                kwargs[f.name] = child.text == "true"
            elif field_type is float:
                kwargs[f.name] = float(child.text)
            elif field_type is int:
                kwargs[f.name] = int(child.text)
            elif isinstance(field_type, type) and issubclass(field_type, StrEnum):
                kwargs[f.name] = field_type(child.text)
            else:
                kwargs[f.name] = child.text
        return state_cls(**kwargs)

    async def _fetch_and_dispatch_state(
        self, node: str, interface: type[Interface], callback: Callable[[Any], None]
    ) -> None:
        """Fetch the current item for *node* and dispatch it to *callback*.

        Called when a live notification arrives without a payload — either a
        retract stanza or a node whose deliver_payloads flag is off.
        """
        try:
            result = await self._safe_send(self.client["xep_0060"].get_items, self._pubsub_service, node, max_items=1)
            item_list = result["pubsub"]["items"]["items"]
            if item_list:
                callback(self._xml_to_dataclass(item_list[0]["payload"], interface.state))
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            pass

    async def _set_state(self, interface: type[Interface], state: Any) -> None:
        node = self._state_node(self._module.name, interface)
        stanza = StateStanza()
        stanza.xml = self._dataclass_to_xml(state, self._state_namespace(interface))
        await self._safe_send(self.client["xep_0060"].publish, self._pubsub_service, node, payload=stanza)

    async def _subscribe_state(self, module: str, interface: type[Interface], callback: Callable[[Any], None]) -> None:
        node = self._state_node(module, interface)
        if node in self._state_node_handlers:
            # Node already subscribed — just add the callback
            self._state_node_handlers[node][1].append(callback)
        else:
            self._state_node_handlers[node] = (interface, [callback])
            await self._safe_send(self.client["xep_0060"].subscribe, self._pubsub_service, node)

        # "deliver the current value immediately on subscribe" -- hard requirement above
        try:
            result = await self._safe_send(self.client["xep_0060"].get_items, self._pubsub_service, node, max_items=1)
            # result["pubsub"]["items"]["items"] uses plugin_multi_attrib to get
            # the list of Item stanzas; item["payload"] returns the XML element
            # via Item.get_payload(). Integer indexing items[0] is wrong here —
            # it calls ElementBase.__getitem__("0") which returns a string.
            item_list = result["pubsub"]["items"]["items"]
            if item_list:
                state_obj = self._xml_to_dataclass(item_list[0]["payload"], interface.state)
                for cb in self._state_node_handlers.get(node, (None, []))[1]:
                    cb(state_obj)
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            pass  # node exists but nothing published yet

    async def _unsubscribe_state(
        self, module: str, interface: type[Interface], callback: Callable[[Any], None]
    ) -> None:
        node = self._state_node(module, interface)
        if node in self._state_node_handlers:
            _, callbacks = self._state_node_handlers[node]
            try:
                callbacks.remove(callback)
            except ValueError:
                pass
            if not callbacks:
                # Last subscriber — unsubscribe from ejabberd and remove handler
                del self._state_node_handlers[node]
                try:
                    await self._safe_send(self.client["xep_0060"].unsubscribe, self._pubsub_service, node)
                except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
                    pass  # already gone server-side


__all__ = ["XmppComm"]
