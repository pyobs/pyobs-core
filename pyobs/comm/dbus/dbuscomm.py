from __future__ import annotations

import asyncio
import copy
import logging
import re
import sys
import types
import inspect
import typing
from collections import OrderedDict
from enum import Enum
from typing import Any, Optional, Type, List, Dict, Tuple, get_args
from dbus_next.aio import MessageBus
import dbus_next.service

from pyobs.comm import Comm
from pyobs.events import ModuleOpenedEvent, ModuleClosedEvent, Event
from pyobs.interfaces import Interface
from pyobs.utils.parallel import Future
from pyobs.utils.types import cast_response_to_real

log = logging.getLogger(__name__)


NONE_VALUES = {str: "NONE", int: sys.maxsize, float: sys.maxsize, list: ["EMPTY"]}


class DbusComm(Comm):
    """A Comm class using cbus.

    This Comm class uses dbus for communication between modules.
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
        self._bus: Optional[MessageBus] = None
        self._dbus_classes: Dict[str, dbus_next.service.ServiceInterface] = {}
        self._dbus_introspection: Optional[dbus_next.proxy_object.BaseProxyObject] = None
        self._interfaces: Dict[str, List[Type[Interface]]] = {}

    async def open(self) -> None:
        """Creates the dbus connection."""

        # create client
        self._bus = await MessageBus().connect()

        # build and publish classes
        self._build_dbus_classes()
        for interface, obj in self._dbus_classes.items():
            self._bus.export("/" + interface.replace(".", "/"), obj)
            await self._bus.request_name(interface)

        # get object for introspection
        introspection = await self._bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
        obj = self._bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus", introspection)
        self._dbus_introspection = obj.get_interface("org.freedesktop.DBus")

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
        if self._bus:
            self._bus.disconnect()

    async def _register_events(
        self,
        events: List[Type[Event]],
        handler: Optional[typing.Callable[[Event, str], typing.Coroutine[Any, Any, bool]]] = None,
    ) -> None:
        print("register event")

    async def _update(self) -> None:
        """Periodic updates."""
        while True:
            await self._update_client_list()
            await asyncio.sleep(5)

    async def _update_client_list(self) -> None:
        """Update list of clients."""

        # get all interfaces containing "pyobs"
        data = list(filter(lambda d: self._domain in d, await self._dbus_introspection.call_list_names()))

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
        for m in list(set(self._interfaces.keys()) - set(interfaces.keys() - {self._name})):
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
            hasattr(annotation, "__origin__")
            and annotation.__origin__ is typing.Union
            and type(None) in get_args(annotation)
        ):
            # optional parameter
            typ = list(filter(lambda x: x is not None, typing.get_args(annotation)))[0]
            return self._annotation_to_dbus(typ)
        elif inspect.isclass(annotation) and issubclass(annotation, Enum):
            return "s"
        else:
            try:
                return {int: "i", float: "d", str: "s", bool: "b", typing.Any: "s"}[annotation]
            except KeyError:
                raise

    def _build_dbus_signature(self, sig: inspect.Signature) -> inspect.Signature:
        # build list of parameters
        new_params: List[inspect.Parameter] = []
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

        # return type
        return_annotation = None if sig.return_annotation is None else self._annotation_to_dbus(sig.return_annotation)

        # create new signature
        return inspect.Signature(parameters=new_params, return_annotation=return_annotation)

    def _build_dbus_classes(self) -> None:
        # got a module?
        if self._module is not None:
            # main module
            main_klass = types.new_class(self._name, bases=(dbus_next.service.ServiceInterface,))

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
            self._dbus_classes[interface] = main_klass(interface)

    def _tuple_to_list(self, sth: Any) -> Any:
        if isinstance(sth, tuple) or isinstance(sth, list):
            return [self._tuple_to_list(a) for a in sth]
        elif isinstance(sth, dict):
            return {k: self._tuple_to_list(v) for k, v in sth.items()}
        else:
            return sth

    def _dbus_function_wrapper(self, method: str, sig: inspect.Signature) -> Any:
        """Function wrapper for dbus methods.

        Args:
            method: Name of method to wrap.

        Returns:
            Wrapper.
        """

        async def inner(this: Any, *args: Any, **kwargs: Any) -> Any:
            # get sender
            sender = None
            if "sender" in kwargs:
                # get client list
                await self._update_client_list()

                # get owner of dbus bus
                sender = await self._get_dbus_owner(kwargs["sender"])
                del kwargs["sender"]

            # insert nones
            print("before insert:", args)
            args = DbusComm._insert_nones(args)
            print("after insert:", args)

            # call method
            return_value = await self.module.execute(method, *args, sender=sender)

            # replace Nones and convert tuples to lists
            return_value = self._tuple_to_list(self._replace_nones(return_value, sig.return_annotation))
            print("return_value:", return_value)

            # return result
            return self._tuple_to_list(return_value)

        inner.__signature__ = self._build_dbus_signature(sig)
        # TODO: Nicer way to do this?
        inner.__dict__["__DBUS_METHOD"] = dbus_next.service._Method(
            inner, method, disabled=False, sender_keyword="sender"
        )
        return inner
        # return dbus_next.service.method(name=method)(inner)

    async def _get_dbus_owner(self, bus: str) -> str:
        """Gets the owning module name for a given bus.

        Params:
            bus: Name of bus to find owner for.

        Returns:
            Owning module.
        """

        # loop all clients, get their owner, and check against bus
        for c in self.clients:
            owner = await self._dbus_introspection.call_get_name_owner(f"{self._domain}.{c}")
            if owner == bus:
                return c

        # nothing found
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

    async def execute(self, client: str, method: str, signature: inspect.Signature, *args: Any) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            signature: Method signature.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        print("execute", client, method, args)

        # get introspection, proxy and interface
        iface = f"{self._domain}.{client}"
        path = "/" + iface.replace(".", "/")
        introspection = await self._bus.introspect(iface, path)
        obj = self._bus.get_proxy_object(iface, path, introspection)
        module = obj.get_interface(iface)

        # cast parameters
        params = []
        for i, arg in enumerate(args, 1):
            # get type of parameter and cast
            annotation = list(signature.parameters.values())[i].annotation
            params.append(DbusComm._replace_nones(arg, annotation))

        print("params:", params)

        # get method and call it
        # TODO: cast some types, like Enums
        func = getattr(module, f"call_{method}")
        res = await func(*params)

        # cast to pyobs
        result = cast_response_to_real(res, signature)
        print("result: ", result)
        return result

    @staticmethod
    def _replace_nones(value: Any, annotation: Any) -> Any:
        """Replace Nones with values of same type.

        Args:
            value: value to check.
            annotation: Annotation for value.

        Returns:
            Same as input value, but no Nones.
        """
        print("_replace_nones", value, annotation)
        print("origin:", typing.get_origin(annotation))

        if value is None and typing.get_origin(annotation) == typing.Union:
            # get types that are not None
            typs = list(filter(lambda x: x is not None, typing.get_args(annotation)))

            # loop them
            for typ in typs:
                print("typ:", typ)
                if typ in NONE_VALUES:
                    print("replace it")
                    return NONE_VALUES[typ]
                elif typing.get_origin(typ) in NONE_VALUES:
                    print("replace it")
                    return NONE_VALUES[typing.get_origin(typ)]
                else:
                    return value

        elif isinstance(value, tuple):
            return tuple(DbusComm._replace_nones(v, a) for v, a in zip(value, get_args(annotation)))
        elif isinstance(value, list):
            typ = get_args(annotation)[0]
            return [DbusComm._replace_nones(v, typ) for v in value]
        elif isinstance(value, dict):
            annk, annv = get_args(annotation)
            return {DbusComm._replace_nones(k, annk): DbusComm._replace_nones(v, annv) for k, v in value.items()}
        elif annotation == typing.Any:
            print("ANY")
            return str(value)
        else:
            return value

    @staticmethod
    def _insert_nones(value: Any) -> Any:
        """Reinsert Nones with values of same type.

        Args:
            value: value to check.

        Returns:
            Same as input value, but no Nones.
        """
        print("_insert_nones", value)

        if value in NONE_VALUES.values():
            return None
        elif isinstance(value, tuple):
            return tuple([DbusComm._insert_nones(v) for v in value])
        elif isinstance(value, list):
            return [DbusComm._insert_nones(v) for v in value]
        elif isinstance(value, dict):
            return {DbusComm._insert_nones(k): DbusComm._insert_nones(v) for k, v in value.items()}
        else:
            return value


__all__ = ["DbusComm"]
