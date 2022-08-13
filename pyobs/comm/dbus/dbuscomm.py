from __future__ import annotations

import inspect
import logging
import types
from typing import Any, Optional, Type, List, Dict
from dbus_next.aio import MessageBus
import dbus_next.service

from pyobs.comm import Comm
from pyobs.interfaces import Interface
from pyobs.utils.parallel import Future

log = logging.getLogger(__name__)


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
        self._methods: Dict[str, Any] = {}

    async def open(self) -> None:
        """Creates the dbus connection.

        Returns:
            Whether opening was successful.
        """

        # create client
        self._bus = await MessageBus().connect()

        self._build_dbus_class()

        # open Comm
        await Comm.open(self)

    async def close(self) -> None:
        """Close connection."""

        # close parent class
        await Comm.close(self)

        # disconnect from dbus
        if self._bus:
            self._bus.disconnect()

    def _dbus_function_wrapper(self, method: str) -> Any:
        @dbus_next.service.method(name=method)
        async def inner(this: Any, *args: Any, **kwargs: Any) -> Any:
            pass

        return inner

    def _build_dbus_class(self) -> None:
        # got a module?
        if self._module is not None:
            # loop all interfaces features
            for i in self._module.interfaces:
                # create class
                klass_name = f"{self._name}_{i.__name__}"
                interface = f"{self._domain}.{self._name}.{i.__name__}"
                klass = types.new_class(klass_name, bases=(dbus_next.service.ServiceInterface,))

                # loop all methods:
                for func_name, func in inspect.getmembers(i, predicate=inspect.isfunction):
                    # set method
                    my_func = types.MethodType(self._dbus_function_wrapper(func_name), self)
                    setattr(klass, func_name, my_func)

                # initialize it
                obj = klass(interface)
                self._dbus_classes[i.__name__] = obj

                # store methods
                for func_name, _ in inspect.getmembers(i, predicate=inspect.isfunction):
                    self._methods[func_name] = getattr(obj, func_name)

                print(klass)

    @property
    def name(self) -> Optional[str]:
        """Name of this client."""
        return self._name

    @property
    def clients(self) -> List[str]:
        return []

    async def get_interfaces(self, client: str) -> List[Type[Interface]]:
        return []

    async def _supports_interface(self, client: str, interface: Type[Interface]) -> bool:
        return True

    async def execute(self, client: str, method: str, signature: inspect.Signature, *args: Any) -> Future:
        return None


__all__ = ["DbusComm"]
