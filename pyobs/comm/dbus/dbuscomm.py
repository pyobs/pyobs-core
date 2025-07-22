# type: ignore
from __future__ import annotations

# patch dbus-next to provide sender name
from .patch import patch  # noqa: F401

import asyncio
import json
import logging
import re
import sys
import types
import inspect
import uuid
from enum import Enum
from typing import (
    Any,
    Optional,
    Type,
    List,
    Dict,
    Tuple,
    get_args,
    Awaitable,
    no_type_check_decorator,
    Union,
    get_origin,
    Protocol,
)
from dbus_next.aio import MessageBus
import dbus_next.service

from pyobs.comm import Comm
from pyobs.events import ModuleOpenedEvent, ModuleClosedEvent, Event
from pyobs.events.event import EventFactory
from pyobs.interfaces import Interface
from pyobs.utils.parallel import Future

log = logging.getLogger(__name__)


NONE_VALUES = {str: "NONE", int: sys.maxsize, float: sys.maxsize, list: ["EMPTY"]}


class ServiceInterface(dbus_next.service.ServiceInterface):
    def __init__(self, interface: str, comm: DbusComm, pyobs_interfaces: List[str]):
        dbus_next.service.ServiceInterface.__init__(self, interface)
        self._interfaces = pyobs_interfaces
        self._comm = comm

    @no_type_check_decorator
    @dbus_next.service.method()
    def get_interfaces(self) -> "as":  # noqa: F722
        return self._interfaces

    @no_type_check_decorator
    @dbus_next.service.method(sender_keyword="sender")
    async def handle_event(self, event: "s", sender):  # noqa: F821
        # convert event to dict
        try:
            d = json.loads(event.replace("'", '"'))
        except json.decoder.JSONDecodeError:
            return

        # create event
        ev = EventFactory.from_dict(d)

        # get real sender
        real_sender = await self._comm.get_dbus_owner(sender)

        # handle it
        await self._comm.handle_event(ev, real_sender)

    @no_type_check_decorator
    @dbus_next.service.method()
    def set_timeout(self, uid: "s", timeout: "d"):  # noqa: F821
        self._comm.set_timeout(uid, timeout)


class DbusMethod(Protocol):
    def __call__(self, *args: Any) -> Any: ...


class DbusComm(Comm):
    """A Comm class using cbus.

    This Comm class uses dbus for communication between modules and is therefore available on all (most) Linux
    systems. The interface name for the bus is build as <domain>.<name> and this class will only find other modules
    with the same domain, so it should be kept constant in a closed system. The name on the other hand should be
    unique in the system.

    A basic configuration looks like this::

        comm:
            class: pyobs.dbus.DbusComm
            name: example
    """

    __module__ = "pyobs.comm.dbus"

    def __init__(
        self,
        name: str,
        domain: str = "org.pyobs.module",
        *args: Any,
        **kwargs: Any,
    ):
        """Create a new dbus Comm module.

        Args:
            name: Name for export.
            domain: Domain for export.
        """
        Comm.__init__(self, *args, **kwargs)

        # variables
        self._name = name
        self._domain = domain
        self._dbus: Optional[MessageBus] = None
        self._dbus_classes: Dict[str, dbus_next.service.ServiceInterface] = {}
        self._dbus_introspection: Optional[dbus_next.aio.ProxyInterface] = None
        self._dbus_introspection_cache: Dict[str, dbus_next.introspection.Node] = {}
        self._interfaces: Dict[str, List[Type[Interface]]] = {}
        self._futures: Dict[str, Future] = {}

    async def open(self) -> None:
        """Creates the dbus connection."""

        # create client
        self._dbus = await MessageBus().connect()
        if not self._dbus:
            raise ValueError("Could not create DBUS connection.")

        # build and publish classes
        self._build_dbus_classes()
        for interface, obj in self._dbus_classes.items():
            self._dbus.export("/" + interface.replace(".", "/"), obj)
            await self._dbus.request_name(interface)

        # get object for introspection
        introspection = await self._dbus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        proxy_object = self._dbus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus", introspection)
        if not proxy_object:
            raise ValueError("Could not fetch proxy object for DBUS.")
        self._dbus_introspection = proxy_object.get_interface("org.freedesktop.DBus")

        # get client list
        await self._update_client_list()

        # update task
        asyncio.create_task(self._update())

        # open Comm
        await Comm.open(self)

    async def close(self) -> None:
        """Close connection."""

        # close parent class
        await Comm.close(self)

        # disconnect from dbus
        if self._dbus:
            self._dbus.disconnect()

    async def _update(self) -> None:
        """Periodic updates."""
        while True:
            await self._update_client_list()
            await asyncio.sleep(5)

    async def _update_client_list(self) -> None:
        """Update list of clients."""

        # check
        if self._dbus_introspection is None:
            return

        # get all interfaces containing "pyobs"
        x = await self._dbus_introspection.call_list_names()
        data = list(filter(lambda d: self._domain in d, x))

        # get all modules: first run regexp on all entries and then cut by length of prefix
        prefix = self._domain + "."
        r = re.compile(prefix + r"(\w+)$")
        modules = list(map(lambda d: d[len(prefix) :], filter(r.match, data)))

        # get interfaces
        interfaces: Dict[str, List[Type[Interface]]] = {}
        for m in modules:
            prefix = f"{self._domain}.{m}.interfaces."
            iface_names = list(map(lambda d: d[len(prefix) :], filter(lambda d: d.startswith(prefix), data)))
            interfaces[m] = self._interface_names_to_classes(iface_names)

        # loop newly connected modules except myself
        for m in list(set(interfaces.keys()) - set(self._interfaces.keys()) - {self._name}):
            # send event
            self._send_event_to_module(ModuleOpenedEvent(), m)

        # loop freshly disconnected modules except myself
        for m in list(set(self._interfaces.keys()) - set(interfaces.keys()) - {self._name}):
            # send event
            self._send_event_to_module(ModuleClosedEvent(), m)

        # store interfaces
        self._interfaces = interfaces

    def _annotation_to_dbus(self, annotation: Any) -> Any:
        if hasattr(annotation, "__origin__") and annotation.__origin__ == list:
            # lists
            return "a" + self._annotation_to_dbus(get_args(annotation)[0])
        elif hasattr(annotation, "__origin__") and annotation.__origin__ == tuple:
            # tuples
            return "(" + "".join([self._annotation_to_dbus(a) for a in get_args(annotation)]) + ")"
        elif hasattr(annotation, "__origin__") and annotation.__origin__ == dict:
            # dicts
            return "a{" + "".join([self._annotation_to_dbus(a) for a in get_args(annotation)]) + "}"
        elif (
            hasattr(annotation, "__origin__") and annotation.__origin__ is Union and type(None) in get_args(annotation)
        ):
            # optional parameter
            typ = list(filter(lambda x: x is not None, get_args(annotation)))[0]
            return self._annotation_to_dbus(typ)
        elif inspect.isclass(annotation) and issubclass(annotation, Enum):
            return "s"
        else:
            try:
                return {int: "i", float: "d", str: "s", bool: "b", Any: "s"}[annotation]
            except KeyError:
                raise

    def _build_dbus_signature(self, sig: inspect.Signature) -> inspect.Signature:
        # build list of parameters
        new_params: List[inspect.Parameter] = []

        # real parameters
        for name, param in sig.parameters.items():
            # ignore kwargs
            if name == "kwargs":
                continue

            # get new annotation
            annotation = param.annotation if name == "self" else self._annotation_to_dbus(param.annotation)

            # build new param
            p = inspect.Parameter(
                name,
                kind=inspect.Parameter.POSITIONAL_ONLY if name == "self" else inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=annotation,
            )

            # store it
            new_params.append(p)

        # add "s" at the end for uid
        new_params.append(inspect.Parameter("uid", kind=inspect.Parameter.KEYWORD_ONLY, annotation="s"))

        # return type
        return_annotation = None if sig.return_annotation is None else self._annotation_to_dbus(sig.return_annotation)

        # create new signature
        return inspect.Signature(parameters=new_params, return_annotation=return_annotation)

    def _build_dbus_classes(self) -> None:
        # got a module?
        if self._module is not None:
            # main module
            main_klass = types.new_class(self._name, bases=(ServiceInterface,))

            # loop all interfaces features
            for i in self._module.interfaces:
                # create class
                klass_name = f"{self._name}_{i.__name__}"
                interface = f"{self._domain}.{self._name}.interfaces.{i.__name__}"
                klass = types.new_class(klass_name, bases=(dbus_next.service.ServiceInterface,))

                # loop all methods:
                for func_name, func in inspect.getmembers(i, predicate=inspect.isfunction):
                    # get signature
                    sig = inspect.signature(func)

                    # set method
                    my_func = types.MethodType(self._dbus_function_wrapper(func_name, sig), self)
                    setattr(main_klass, func_name, my_func)

                # initialize it
                self._dbus_classes[interface] = klass(interface)

            # initialize main class
            interface = f"{self._domain}.{self._name}"
            self._dbus_classes[interface] = main_klass(interface, self, [i.__name__ for i in self._module.interfaces])

    async def _get_dbus_introspection(self, client: str) -> Tuple[dbus_next.introspection.Node, str, str]:
        # check
        if self._dbus is None:
            raise ValueError("No connection")

        # get interface and path
        interface = f"{self._domain}.{client}"
        path = "/" + interface.replace(".", "/")

        # get introspection and return it
        if client not in self._dbus_introspection_cache:
            self._dbus_introspection_cache[client] = await self._dbus.introspect(interface, path)
        return self._dbus_introspection_cache[client], interface, path

    async def _get_dbus_method(self, client: str, method: str) -> DbusMethod:
        # check
        if self._dbus is None:
            raise ValueError("No connection")

        # get introspection, interface and path
        introspection, interface, path = await self._get_dbus_introspection(client)

        # get object and module
        obj = self._dbus.get_proxy_object(interface, path, introspection)
        module = obj.get_interface(interface)

        # get function
        return getattr(module, f"call_{method}")

    def _dbus_function_wrapper(self, method: str, sig: inspect.Signature) -> Any:
        """Function wrapper for dbus methods.

        Args:
            method: Name of method to wrap.

        Returns:
            Wrapper.
        """

        async def inner(this: Any, *args: Any, **kwargs: Any) -> Any:
            # check
            if self.module is None:
                return

            # get sender
            sender = None
            if "sender" in kwargs:
                # get real sender
                sender = await self.get_dbus_owner(kwargs["sender"])
                del kwargs["sender"]

            # get uid
            uid = args[-1]
            args = args[:-1]

            # get method
            func, signature, _ = self._module.methods[method]

            # bind parameters
            ba = signature.bind(*args)
            ba.apply_defaults()

            # do we have a timeout?
            if hasattr(func, "timeout") and sender is not None:
                timeout = await getattr(func, "timeout")(self._module, **ba.arguments)
                if timeout:
                    # get introspection, proxy and interface
                    set_timeout = await self._get_dbus_method(sender, "set_timeout")
                    await set_timeout(uid, int(timeout))

            # call method
            return await self.module.execute(method, *args, sender=sender)

        # set signature
        inner.__signature__ = self._build_dbus_signature(sig)
        # TODO: Nicer way to do this?
        inner.__dict__["__DBUS_METHOD"] = dbus_next.service._Method(
            inner, method, disabled=False, sender_keyword="sender"
        )
        return inner
        # return dbus_next.service.method(name=method)(inner)

    async def get_dbus_owner(self, bus: str, attempts: int = 3) -> str:
        """Gets the owning module name for a given bus.

        Params:
            bus: Name of bus to find owner for.

        Returns:
            Owning module.
        """

        # check
        if self._dbus_introspection is None:
            raise ValueError("No connection.")

        # loop all clients, get their owner, and check against bus
        for c in self.clients:
            try:
                owner = await self._dbus_introspection.call_get_name_owner(f"{self._domain}.{c}")
            except dbus_next.errors.DBusError:
                break
            if owner == bus:
                return c

        # nothing found
        if attempts > 0:
            await asyncio.sleep(0.5)
            await self._update_client_list()
            return await self.get_dbus_owner(bus, attempts - 1)
        else:
            raise ValueError("Owner not found.")

    @property
    def name(self) -> Optional[str]:
        """Name of this client."""
        return self._name

    @property
    def clients(self) -> List[str]:
        """Returns list of currently connected clients.

        Returns:
            (list) List of currently connected clients.
        """

        # return names
        return list(self._interfaces.keys())

    async def get_interfaces(self, client: str) -> List[Type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """

        # return list
        return self._interfaces[client]

    async def _supports_interface(self, client: str, interface: Type[Interface]) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether or not interface is supported.
        """

        # does it exist?
        return interface in self._interfaces[client]

    async def execute(self, client: str, method: str, annotation: Dict[str, Any], *args: Any) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            annotation: Method annotation.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """

        # check
        if self._dbus is None:
            raise ValueError("No connection.")

        # create a future for this
        uid = str(uuid.uuid4())
        future = Future(annotation=annotation, comm=self)
        self._futures[uid] = future

        # get method
        func = await self._get_dbus_method(client, method)

        # get method and call it in background
        asyncio.create_task(self._wait_for_method(func(*args, uid), uid))

        # don't wait for response, just return future
        return await future

    async def _wait_for_method(self, func: Awaitable[Any], uid: str) -> None:
        # wait for result
        result = await func

        # set result
        self._futures[uid].set_result(result)

    def cast_to_simple_pre(self, value: Any, annotation: Optional[Any] = None) -> Tuple[bool, Any]:
        """Special treatment of single parameters when converting them to be sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """

        if annotation == Any:
            # cast Anys to string
            return True, str(value)

        elif value is None and get_origin(annotation) == Union:
            # get types that are not None
            typs = list(filter(lambda x: x is not None, get_args(annotation)))

            # loop them
            for typ in typs:
                if typ in NONE_VALUES:
                    return True, NONE_VALUES[typ]
                elif get_origin(typ) in NONE_VALUES:
                    return True, NONE_VALUES[get_origin(typ)]
                else:
                    return True, value
            else:
                return True, value

        elif isinstance(value, tuple):
            return False, list(value)

        else:
            return False, value

    def cast_to_real_pre(self, value: Any, annotation: Optional[Any] = None) -> Tuple[bool, Any]:
        """Special treatment of single parameters when converting them after being sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """

        if annotation == Any:
            # try to guess type
            try:
                f = float(value)
                i = int(f)
                return True, i if f == i and "." not in value else f
            except ValueError:
                return True, value
        elif value in NONE_VALUES.values():
            return True, None
        else:
            return False, value

    async def send_event(self, event: Event) -> None:
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """

        # check
        if self._dbus is None:
            raise ValueError("No connection.")

        # loop all clients
        for client in self.clients:
            # skip myself
            if client == self._name:
                continue

            # get function
            try:
                func = await self._get_dbus_method(client, "handle_event")
            except ValueError:
                # client offline?
                continue

            # call it
            await func(json.dumps(event.to_json()))

    async def handle_event(self, event: Event, sender: str) -> None:
        """Handle event localy, i.e. send it to module.

        Args:
            event: Event to handle.
            sender: Sender of event.
        """
        self._send_event_to_module(event, sender)

    def set_timeout(self, uid: str, timeout: float) -> None:
        """Set timeout, usually received from other module.

        Args:
            uid: UID of remote call.
            timeout: Timeout in seconds.
        """
        self._futures[uid].set_timeout(timeout)


__all__ = ["DbusComm"]
