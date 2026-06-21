from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, overload

import pyobs.interfaces
from pyobs.events import Event, LogEvent, ModuleClosedEvent
from pyobs.interfaces import Interface

from .commlogging import CommLoggingHandler
from .proxy import Proxy, ProxyType, _ProxyContext

if TYPE_CHECKING:
    from pyobs.modules import Module

log = logging.getLogger(__name__)


class Comm:
    """Base class for all Comm modules in pyobs."""

    __module__ = "pyobs.comm"

    def __init__(self) -> None:
        """Creates a comm module."""

        self._proxies: dict[str, Proxy] = {}
        self._module: Module | None = None
        self._log_queue: asyncio.Queue[LogEvent] = asyncio.Queue()
        self._logging_task: asyncio.Task[Any] | None = None
        self._event_handlers: dict[type[Event], list[Callable[[Event, str], Coroutine[Any, Any, bool]]]] = {}
        self._closing = asyncio.Event()

    @property
    def has_module(self) -> bool:
        return self._module is not None

    @property
    def module(self) -> Module:
        """The module that this Comm object is attached to."""
        if self._module is None:
            raise ValueError("No module.")
        return self._module

    @module.setter
    def module(self, module: Module) -> None:
        """The module that this Comm object is attached to."""
        # if we have a _set_module method, call it
        self._set_module(module)

        # store module
        self._module = module

    def _set_module(self, module: Module) -> None: ...

    async def open(self) -> None:
        """Open module."""

        # add handler to global logger
        handler = CommLoggingHandler(self)
        handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(handler)

        # start logging thread
        self._logging_task = asyncio.create_task(self._logging())

        # some events
        await self.register_event(ModuleClosedEvent, self._client_disconnected)

    async def close(self) -> None:
        """Close module."""

        self._closing.set()

        # close thread
        if self._logging_task:
            self._logging_task.cancel()
        self._logging_task = None

    def _get_full_client_name(self, name: str) -> str:
        """Returns full name for given client.

        Some Comm modules may use short names for their clients. This methods returns the full name
        for a given short name.

        Args:
            name: Short name to get full name for.

        Returns:
            Full name for given client.
        """

        # this base class doesn't have short names
        return name

    async def _get_client(self, client: str) -> Module | Proxy | None:
        """Get a proxy to the given client.

        Args:
            client: Name of client.

        Returns:
            Proxy class for given client.
        """

        # return module, if "main" is requested
        if client == "main":
            return self.module
        if client is None:
            return None

        # if client doesn't exist or we disabled caching, fetch a new proxy
        if client not in self._proxies:
            # get interfaces
            try:
                interfaces = await self.get_interfaces(client)
            except IndexError:
                return None

            # create new proxy
            proxy = Proxy(self, client, interfaces)
            self._proxies[client] = proxy

        # return proxy
        return self._proxies[client]

    async def _resolve_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> Any | ProxyType:
        """Returns object directly if it is of given type. Otherwise get proxy of client with given name and check type.

        If name_or_object is an object:
            - If it is of type (or derived), return object.
            - Otherwise raise exception.
        If name_name_or_object is string:
            - Create proxy from name and raise exception, if it doesn't exist.
            - Check type and raise exception if wrong.
            - Return object.

        Args:
            name_or_object: Name of object or object itself.
            obj_type: Expected class of object.

        Returns:
            Object or proxy to object.

        Raises:
            ValueError: If proxy does not exist or wrong type.
        """

        if obj_type is not None and isinstance(name_or_object, obj_type):
            # return directly
            return name_or_object

        elif isinstance(name_or_object, str):
            # get proxy
            try:
                proxy = await self._get_client(name_or_object)
            except KeyError:
                raise ValueError(f"Could not get proxy for {name_or_object}.")

            # check it
            if proxy is None:
                raise ValueError(f'Could not create proxy for given name "{name_or_object}".')
            elif obj_type is None or isinstance(proxy, obj_type):
                return proxy
            else:
                raise ValueError(
                    f'Proxy obtained from given name "{name_or_object}" is not of requested type "{obj_type}".'
                )

        else:
            # completely wrong...
            raise ValueError(f'Given parameter is neither a name nor an object of requested type "{obj_type}".')

    async def _safe_resolve_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> Any | ProxyType | None:
        """Calls proxy() in a safe way and returns None instead of raising an exception."""

        try:
            return await self._resolve_proxy(name_or_object, obj_type)
        except ValueError:
            return None

    @overload
    def proxy(self, name_or_object: str | object, obj_type: type[ProxyType]) -> _ProxyContext[ProxyType]: ...
    @overload
    def proxy(self, name_or_object: str | object, obj_type: None = None) -> _ProxyContext[Any]: ...

    def proxy(self, name_or_object: str | object, obj_type: type[ProxyType] | None = None) -> _ProxyContext[Any]:
        """Returns a context manager; use as `async with self.proxy(...) as x:`."""
        return _ProxyContext(self._resolve_proxy(name_or_object, obj_type))

    @overload
    def safe_proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType]
    ) -> _ProxyContext[ProxyType | None]: ...
    @overload
    def safe_proxy(self, name_or_object: str | object, obj_type: None = None) -> _ProxyContext[Any]: ...

    def safe_proxy(self, name_or_object: str | object, obj_type: type[ProxyType] | None = None) -> _ProxyContext[Any]:
        """Same as proxy(), but yields None inside the block instead of raising."""
        return _ProxyContext(self._safe_resolve_proxy(name_or_object, obj_type))

    async def _client_disconnected(self, event: Event, sender: str) -> bool:
        """Called when a client disconnects.

        Args:
            event: Disconnect event.
            sender: Name of client that disconnected.

        """

        # if a client disconnects, we remove its proxy
        if sender in self._proxies:
            del self._proxies[sender]
        return True

    @property
    def name(self) -> str | None:
        """Name of this client."""
        raise NotImplementedError

    @property
    def clients(self) -> list[str]:
        """Returns list of currently connected clients.

        Returns:
            (list) list of currently connected clients.
        """
        raise NotImplementedError

    async def clients_with_interface(self, interface: type[Interface]) -> list[str]:
        """Returns list of currently connected clients that implement the given interface.

        Args:
            interface: Interface to search for.

        Returns:
            (list) list of currently connected clients that implement the given interface.
        """
        return [c for c in self.clients if await self._supports_interface(c, interface)]

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            list of supported interfaces.

        Raises:
            IndexError: If client cannot be found.
        """
        raise NotImplementedError

    async def _supports_interface(self, client: str, interface: type[Interface]) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether or not interface is supported.
        """
        raise NotImplementedError

    @staticmethod
    def _interface_names_to_classes(interfaces: list[str]) -> list[type[Interface]]:
        """Converts a list of interface names to interface classes.

        Args:
            interfaces: list of interface names.

        Returns:
            list of interface classes.
        """

        # get interface classes
        inspection = inspect.getmembers(pyobs.interfaces, predicate=inspect.isclass)

        # loop interfaces
        interface_classes = []
        for interface_name in interfaces:
            # loop all classes
            found = False
            for cls_name, cls in inspection:
                # class needs to face same name and implement Interface
                if interface_name == cls_name and issubclass(cls, Interface):
                    # found it!
                    found = True

                    # then add it to the list of all interfaces
                    interface_classes.append(cls)

                    # there can only be one...
                    break

            # not found?
            if not found:
                log.error('Could not find interface "%s" for client.', interface_name)
        return interface_classes

    async def execute(self, client: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        """Execute a given method on a remote client.

        Args:
            client (str): ID of client.
            method (str): Method to call.
            annotation: Method annotation.
            *args: list of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        raise NotImplementedError

    async def _logging(self) -> None:
        """Background thread for handling the logging."""
        # run until closing
        while True:
            # get item (maybe wait for it) and send it
            try:
                entry = self._log_queue.get_nowait()
                await self.send_event(entry)

            except asyncio.QueueEmpty:
                # if queue is empty, sleep a little
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                return

            except Exception:
                log.exception("Something went wrong")
                pass

    def log_message(self, entry: LogEvent) -> None:
        """Send a log message to other clients.

        Args:
            entry (LogEvent): Log event to send.
        """
        self._log_queue.put_nowait(entry)

    async def send_event(self, event: Event) -> None:
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """
        pass

    def _get_derived_events(self, event: type[Event]) -> list[type[Event]]:
        """Return list of given event itself and all events derived from it.

        Args:
            event: Event class to check.

        Returns:
            list of event classes.
        """
        import pyobs.events

        event_classes: list[type[Event]] = []
        for cls in inspect.getmembers(pyobs.events, inspect.isclass):
            if issubclass(cls[1], event):
                event_classes.append(cls[1])
        return event_classes

    async def register_event(
        self, event_class: type[Event], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None:
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

    async def _register_events(
        self, events: list[type[Event]], handler: Callable[[Event, str], Coroutine[Any, Any, bool]] | None = None
    ) -> None:
        pass

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

    def cast_to_simple_pre(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them to be sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """
        return False, value

    def cast_to_simple_post(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them to be sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """
        return False, value

    def cast_to_real_pre(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them after being sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """
        return False, value

    def cast_to_real_post(self, value: Any, annotation: Any | None = None) -> tuple[bool, Any]:
        """Special treatment of single parameters when converting them after being sent via Comm.

        Args:
            value: Value to be treated.
            annotation: Annotation for value.

        Returns:
            A tuple containing a tuple that indicates whether this value should be further processed and a new value.
        """
        return False, value


__all__ = ["Comm"]
