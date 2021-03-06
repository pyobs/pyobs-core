import inspect
import logging
import queue
from typing import Any, Union, Type, Dict
import threading

import pyobs.interfaces
from pyobs.events import Event, LogEvent, ModuleOpenedEvent, ModuleClosedEvent
from .proxy import Proxy
from .sharedvariablecache import SharedVariableCache
from .commlogging import CommLoggingHandler


log = logging.getLogger(__name__)


class Comm:
    """Base class for all Comm modules in pyobs."""

    def __init__(self, cache_proxies: bool = True, *args, **kwargs):
        """Creates a comm module."""

        self._proxies: Dict[str, Proxy] = {}
        self._module = None
        self._log_queue = queue.Queue()
        self._cache_proxies = cache_proxies

        # cache for shared variables
        self.variables = SharedVariableCache(comm=self)

        # add handler to global logger
        handler = CommLoggingHandler(self)
        handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(handler)

        # logging thread
        self._closing = threading.Event()
        self._logging_thread = threading.Thread(target=self._logging)

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, module):
        # if we have a _set_module method, call it
        if hasattr(self, '_set_module'):
            self._set_module(module)

        # store module
        self._module = module

    def open(self):
        """Open module."""

        # start logging thread
        self._logging_thread.start()

        # open variables cache
        self.variables.open()

        # some events
        self.register_event(ModuleClosedEvent, self._client_disconnected)

    def close(self):
        """Close module."""

        # close thread
        self._closing.set()
        self._logging_thread.join()

        # close variables cache
        self.variables.close()

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

    def __getitem__(self, client: str) -> Proxy:
        """Get a proxy to the given client.

        Args:
            client: Name of client.

        Returns:
            Proxy class for given client.
        """

        # return module, if "main" is requested
        if client == 'main':
            return self.module
        if client is None:
            return None

        # if client doesn't exist or we disabled caching, fetch a new proxy
        if client not in self._proxies or not self._cache_proxies:
            # get interfaces
            try:
                interfaces = self.get_interfaces(client)
            except IndexError:
                return None

            # create new proxy
            proxy = Proxy(self, client, interfaces)
            self._proxies[client] = proxy

        # return proxy
        return self._proxies[client]

    def proxy(self, name_or_object: Union[str, object], obj_type: Type = None):
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
            proxy = self[name_or_object]

            # check it
            if proxy is None:
                raise ValueError('Could not create proxy for given name "%s".' % name_or_object)
            elif obj_type is None or isinstance(proxy, obj_type):
                return proxy
            else:
                raise ValueError('Proxy obtained from given name "%s" is not of requested type "%s".' %
                                 (name_or_object, obj_type))

        else:
            # completely wrong...
            raise ValueError('Given parameter is neither a name nor an object of requested type "%s".' % obj_type)

    def _client_disconnected(self, event: ModuleClosedEvent, sender: str, *args, **kwargs):
        """Called when a client disconnects.

        Args:
            event: Disconnect event.
            sender: Name of client that disconnected.

        """

        # if a client disconnects, we remove its proxy
        if sender in self._proxies:
            del self._proxies[sender]

    @property
    def name(self) -> str:
        """Name of this client."""
        raise NotImplementedError

    @property
    def clients(self) -> list:
        """Returns list of currently connected clients.

        Returns:
            (list) List of currently connected clients.
        """
        raise NotImplementedError

    def clients_with_interface(self, interface) -> list:
        """Returns list of currently connected clients that implement the given interface.

        Args:
            interface: Interface to search for.

        Returns:
            (list) List of currently connected clients that implement the given interface.
        """
        return list(filter(lambda c: self._supports_interface(c, interface), self.clients))

    def get_interfaces(self, client: str) -> list:
        """Returns list of interfaces for given client.

        Args:
            client: Name of client.

        Returns:
            List of supported interfaces.

        Raises:
            IndexError, if client cannot be found.
        """
        raise NotImplementedError

    def _supports_interface(self, client: str, interface: str) -> bool:
        """Checks, whether the given client supports the given interface.

        Args:
            client: Client to check.
            interface: Interface to check.

        Returns:
            Whether or not interface is supported.
        """
        raise NotImplementedError

    @staticmethod
    def _interface_names_to_classes(interfaces: list) -> list:
        """Converts a list of interface names to interface classes.

        Args:
            interfaces: List of interface names.

        Returns:
            List of interface classes.
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
                if interface_name == cls_name and issubclass(cls, pyobs.interfaces.Interface):
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

    def add_command_handler(self, command: str, handler):
        """Add a command handler.

        Args:
            command (str): Name of command to handle.
            handler: Method that handles the command
        """
        raise NotImplementedError

    def del_command_handler(self, command: str, handler):
        """Delete a command handler.

        Args:
            command: Name of command to handle.
            handler: Method that handles the command
        """
        raise NotImplementedError

    def send_text_message(self, client: str, msg: str):
        """Send a text message to another client.

        Args:
            client: ID of client to send message to.
            msg: Message to send.
        """
        raise NotImplementedError

    def execute(self, client: str, method: str, *args) -> Any:
        """Execute a given method on a remote client.

        Args:
            client: ID of client.
            method: Method to call.
            *args: List of parameters for given method.

        Returns:
            Passes through return from method call.
        """
        raise NotImplementedError

    def _logging(self):
        """Background thread for handling the logging."""

        # run until closing
        while not self._closing.is_set():
            # do we have a message in the queue?
            while not self._log_queue.empty():
                # get item and send it
                entry = self._log_queue.get_nowait()
                self.send_event(entry)

            # sleep a little
            self._closing.wait(1)

    def log_message(self, entry: LogEvent):
        """Send a log message to other clients.

        Args:
            entry (LogEvent): Log event to send.
        """
        self._log_queue.put_nowait(entry)

    def send_event(self, event: Event):
        """Send an event to other clients.

        Args:
            event (Event): Event to send
        """
        pass

    def register_event(self, event_class, handler=None):
        """Register an event type. If a handler is given, we also receive those events, otherwise we just
        send them.

        Args:
            event_class: Class of event to register.
            handler: Event handler method.
        """
        pass


__all__ = ['Comm']
