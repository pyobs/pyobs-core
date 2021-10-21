from __future__ import annotations
import inspect
import types
from typing import TYPE_CHECKING, Any, Type, List, Dict

from pyobs.interfaces import Interface
from pyobs.utils.threads.future import BaseFuture
from pyobs.utils.types import cast_bound_arguments_to_simple
import pyobs.interfaces.proxies
if TYPE_CHECKING:
    from pyobs.comm import Comm


class Proxy:
    """A proxy for remote pyobs modules."""
    __module__ = 'pyobs.comm'

    def __init__(self, comm: 'Comm', client: str, interfaces: List[Type[Interface]]):
        """Creates a new proxy.

        Args:
            comm: Comm object to use for connection.
            client: Name of client to connect to.
            interfaces: List of interfaces supported by client.
        """

        # set client and interfaces
        self._comm: Comm = comm
        self._client = client
        self._interfaces = interfaces

        # remove interfaces that are implemented by others
        to_delete = []
        for i1 in interfaces:
            for i2 in interfaces:
                if i1 != i2 and issubclass(i1, i2):
                    # i1 implements i2, so remove i2
                    to_delete.append(i2)
        interfaces = [i for i in interfaces if i not in to_delete]

        # interface proxies
        interface_proxies = []
        for iface in interfaces:
            interface_proxies.append(getattr(pyobs.interfaces.proxies, iface.__name__ + 'Proxy'))

        # add interfaces as base classes
        cls = self.__class__
        self.__class__ = cls.__class__("Proxy", tuple([cls] + interface_proxies), {})  # type: ignore

        # create methods
        self._methods = self._create_methods()

    @property
    def name(self) -> str:
        """Name of the client."""
        return self._client

    @property
    def method_names(self) -> List[str]:
        """List of method names."""
        return list(sorted(self._methods.keys()))

    @property
    def interfaces(self) -> List[Type[Interface]]:
        """List of interfaces."""
        return self._interfaces

    def signature(self, method: str) -> inspect.Signature:
        """Returns the signature of a given method.

        Args:
            method: Name of the method.

        Returns:
            Signature of the given method.
        """
        return inspect.signature(self._methods[method][0])

    def interface_method(self, method: str) -> Any:
        """Returns the method of the given name from the interface and not from the object itself.

        Args:
            method: Name of method.

        Returns:
            The interface method.
        """
        return self._methods[method][0]

    def execute(self, method: str, *args: Any, **kwargs: Any) -> BaseFuture:
        """Execute a method on the remote client.

        Args:
            method: Name of method to call.
            *args: Parameters for  method call.
            **kwargs: Parameters for method call.

        Returns:
            Result of method call.
        """

        # add 'self' to args
        args = tuple([self] + list(args))

        # get method signature and bind it
        signature = inspect.signature(self._methods[method][0])
        ba = signature.bind(*args, **kwargs)
        ba.apply_defaults()

        # cast to simple types
        cast_bound_arguments_to_simple(ba)

        # do request and return future
        return self._comm.execute(self._client, method, signature, *ba.args[1:])

    def _create_methods(self) -> Dict[str, Any]:
        """Create local methods for the remote client."""

        # loop all interfaces and get methods
        methods = {}
        for interface in self._interfaces:
            # loop all methods:
            for func_name, func in inspect.getmembers(interface, predicate=inspect.isfunction):
                # set method
                my_func = types.MethodType(self._remote_function_wrapper(func_name), self)
                setattr(self, func_name, my_func)

                # store func
                methods[func_name] = (func, getattr(self, func_name))

        # return methods
        return methods

    def _remote_function_wrapper(self, method: str) -> Any:
        """Function wrapper for remote calls.

        Args:
            method: Name of method to wrap.

        Returns:
            Wrapper.
        """

        def inner(this: 'Proxy', *args: Any, **kwargs: Any) -> Any:
            return this.execute(method, *args, **kwargs)

        return inner


__all__ = ['Proxy']
