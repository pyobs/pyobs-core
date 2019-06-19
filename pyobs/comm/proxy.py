import inspect
import types

from pyobs.utils.types import cast_bound_arguments_to_real, cast_response_to_real, cast_bound_arguments_to_simple


class Proxy:
    """A proxy for remote pyobs modules."""

    def __init__(self, comm: 'Comm', client: str, interfaces: list):
        """Creates a new proxy.

        Args:
            comm: Comm object to use for connection.
            client: Name of client to connect to.
            interfaces: List of interfaces supported by client.
        """

        # set client and interfaces
        self._comm = comm
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

        # add interfaces as base classes
        cls = self.__class__
        self.__class__ = cls.__class__("Proxy", tuple([cls] + interfaces), {})

        # create methods
        self._methods = self._create_methods()

    @property
    def name(self):
        """Name of the client."""
        return self._client

    @property
    def method_names(self):
        """List of method names."""
        return list(sorted(self._methods.keys()))

    @property
    def interfaces(self):
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

    def interface_method(self, method: str):
        """Returns the method of the given name from the interface and not from the object itself.

        Args:
            method: Name of method.

        Returns:
            The interface method.
        """
        return self._methods[method][0]

    def execute(self, method, *args, **kwargs):
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
        future = self._comm.execute(self._client, method, *ba.args[1:])
        future.set_signature(signature)
        return future

    def _create_methods(self):
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

    def _remote_function_wrapper(self, method):
        """Function wrapper for remote calls.

        Args:
            method: Name of method to wrap.

        Returns:
            Wrapper.
        """

        def inner(self, *args, **kwargs):
            return self.execute(method, *args, **kwargs)

        return inner


__all__ = ['Proxy']
