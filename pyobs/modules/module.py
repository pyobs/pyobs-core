from __future__ import annotations
import asyncio
import inspect
import logging
import typing
from typing import Union, Type, Any, Callable, Dict, Tuple, List, TypeVar, Optional, cast
from py_expression_eval import Parser
import packaging.version

from pyobs.events import ModuleOpenedEvent, Event
from pyobs.object import Object
from pyobs.interfaces import IModule, IConfig, Interface
from pyobs.utils.enums import ModuleState
from pyobs.utils.types import cast_bound_arguments_to_real, cast_response_to_simple
from pyobs.version import version
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Any])


def timeout(func_timeout: Union[str, int, Callable[..., Any], None] = None) -> Callable[[F], F]:
    """Decorates a method with information about timeout for an async HTTP call.

    :param func_timeout:  Integer or string that specifies the timeout.
                          If string, it is parsed using the variables in kwargs.
    """

    def timeout_decorator(func: F) -> F:
        async def _timeout(obj: Any, *args: Any, **kwargs: Any) -> float:
            # define variables as non-local
            nonlocal func_timeout, func

            # init to 0 second
            to = 0.0

            # do we have a timeout?
            if func_timeout is not None:
                # what is it?
                if callable(func_timeout):
                    # this is a method, does it have a timeout on it's own? then use it
                    try:
                        if hasattr(func_timeout, "timeout"):
                            # call timeout method, only works if this has the same parameters
                            to = await getattr(func_timeout, "timeout")(obj, *args, **kwargs)
                        else:
                            # call method directly
                            to = await func_timeout(obj, *args, **kwargs)
                    except:
                        log.exception("Could not call timeout method.")

                elif isinstance(func_timeout, str):
                    # this is a string with a function, so evaluate it
                    try:
                        parser = Parser()
                        to = parser.parse(func_timeout).evaluate(kwargs)
                    except Exception:
                        log.error('Could not find timeout "%s" in list of parameters.', func_timeout)

                else:
                    # it's a number, add timeout directly
                    try:
                        to = float(func_timeout)
                    except ValueError:
                        log.exception("Could not convert timeout to float.")
                        to = 0.0

            # return it
            return to

        # decorate method
        setattr(func, "timeout", _timeout)
        return func

    return timeout_decorator


class Module(Object, IModule, IConfig):
    """Base class for all pyobs modules."""

    __module__ = "pyobs.modules"

    def __init__(
        self,
        name: Optional[str] = None,
        label: Optional[str] = None,
        own_comm: bool = True,
        additional_config_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """
        Args:
            name: Name of module. If None, ID from comm object is used.
            label: Label for module. If None, name is used.
            own_comm: If True, module owns comm and opens/closes it.
            additional_config_variables: List of additional variable names available to remote config getter/setter.
        """
        Object.__init__(self, **kwargs)

        # get list of client interfaces
        self._interfaces: List[Type[Interface]] = []
        self._methods: Dict[str, Tuple[Callable[..., Any], inspect.Signature, Dict[Any, Any]]] = {}
        self._get_interfaces_and_methods()

        # get configuration caps, i.e. all parameters from c'tor
        self._additional_config_variables = additional_config_variables
        self._config_caps = self._get_config_caps()

        # name and label
        self._device_name = name if name is not None else self.comm.name
        self._label = label if label is not None else self._device_name

        # state
        self._state = ModuleState.READY
        self._error_string = ""

        # own?
        self._own_comm = own_comm

        # close
        self._closing = asyncio.Event()

    async def open(self) -> None:
        # open comm
        if self.comm is not None and self._own_comm:
            # open it and connect module
            self.comm.module = self
            await self.comm.open()

            # react to connecting modules
            await self.comm.register_event(ModuleOpenedEvent, self._on_module_opened)

        """Open module."""
        await Object.open(self)

    async def close(self) -> None:
        """Close module."""
        await Object.close(self)

        # close comm
        if self.comm is not None and self._own_comm:
            log.info("Closing connection to server...")
            await self.comm.close()

    @staticmethod
    def new_event_loop() -> asyncio.AbstractEventLoop:
        return asyncio.new_event_loop()

    async def main(self) -> None:
        """Main loop for application."""
        await self._closing.wait()

    @property
    def name(self) -> str:
        """Returns name of module."""
        return "" if self._device_name is None else self._device_name

    async def get_label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        return "" if self._label is None else self._label

    async def get_version(self, **kwargs: Any) -> str:
        """Returns pyobs version of module."""
        return version()

    async def _on_module_opened(self, event: Event, sender: str) -> bool:
        """React to other modules connecting."""
        if sender == self.comm.name or not isinstance(event, ModuleOpenedEvent):
            return False

        # get proxy and version
        proxy = await self.proxy(sender, IModule)
        try:
            module_version = await proxy.get_version()
        except exc.RemoteError:
            return True

        # log it
        log.debug(f"Other module {sender} found, running on pyobs {module_version}.")

        # check version, only compare major and minor, ignore patch level
        v1, v2 = packaging.version.parse(version()), packaging.version.parse(module_version)
        if v1.major != v2.major or v1.minor != v2.minor:
            log.critical(
                f'Found module "{sender}" with different pyobs version {module_version} (≠{version()}), '
                f"please update pyobs."
            )

        # okay
        return True

    @property
    def interfaces(self) -> List[Type[Interface]]:
        """List of implemented interfaces."""
        return self._interfaces

    @property
    def methods(self) -> Dict[str, Tuple[Callable[..., Any], inspect.Signature, Dict[Any, Any]]]:
        """List of methods."""
        return self._methods

    def _get_interfaces_and_methods(self) -> None:
        """List interfaces and methods of this module."""
        import pyobs.interfaces

        # get interfaces
        self._interfaces = []
        self._methods = {}
        for _, interface in inspect.getmembers(pyobs.interfaces, predicate=inspect.isclass):
            # is module a sub-class of that class that inherits from Interface?
            if isinstance(self, interface) and issubclass(interface, pyobs.interfaces.Interface):
                # we ignore the interface "Interface"
                if interface == pyobs.interfaces.Interface:
                    continue

                # add interface
                self._interfaces += [interface]

                # loop methods of that interface
                for method_name, method in inspect.getmembers(interface, predicate=inspect.isfunction):
                    # get method and signature
                    func = getattr(self, method_name)
                    signature = inspect.signature(func)
                    type_hints = typing.get_type_hints(func)

                    # fill dict of name->(method, signature)
                    self._methods[method_name] = (func, signature, type_hints)

    def quit(self) -> None:
        """Quit module."""
        self._closing.set()
        asyncio.get_event_loop().stop()

    async def execute(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a local method safely with type conversion

        All incoming variables in args and kwargs must be of simple type (i.e. int, float, str, bool, tuple) and will
        be converted to the requested type automatically. All outgoing variables are converted to simple types
        automatically as well.

        Args:
            method: Name of method to execute.
            *args: Parameters for method.
            **kwargs: Parameters for method.

        Returns:
            Response from method call.

        Raises:
            KeyError: If method does not exist.
        """

        # is module in error state?
        if self._state == ModuleState.ERROR:
            # if called method is not from IModule, raise error
            if not hasattr(IModule, method):
                raise exc.ModuleError("Module is in error state, please reset it.")

        # get method and signature (may raise KeyError)
        func, signature, type_hints = self._methods[method]

        # bind parameters
        ba = signature.bind(*args, **kwargs)
        ba.apply_defaults()

        # get additional args and kwargs and delete from ba
        func_args = []
        func_kwargs = {}
        if "args" in ba.arguments:
            func_args = ba.arguments["args"]
            del ba.arguments["args"]
        if "kwargs" in ba.arguments:
            func_kwargs = ba.arguments["kwargs"]
            del ba.arguments["kwargs"]

        # cast to types requested by method
        cast_bound_arguments_to_real(ba, type_hints, self.comm.cast_to_real_pre, self.comm.cast_to_real_post)

        # call method
        response = await func(*func_args, **ba.arguments, **func_kwargs)

        # finished
        return cast_response_to_simple(
            response, type_hints["return"], self.comm.cast_to_simple_pre, self.comm.cast_to_simple_post
        )

    def _get_config_caps(self) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns a dictionary with config caps."""

        # init dict of caps and types
        caps: Dict[str, Tuple[bool, bool, bool]] = {}

        # loop super classes
        for cls in inspect.getmro(self.__class__):
            # ignore Object and Module
            if cls in [Object, Module]:
                continue

            # get signature
            sig = inspect.signature(getattr(cls, "__init__"))
            for name in sig.parameters:
                # ignore self, args, kwargs
                if name in ["self", "args", "kwargs"]:
                    continue

                # add it
                caps[name] = self._add_config_cap(name)

            # also add all additional config vars
            if self._additional_config_variables:
                for name in self._additional_config_variables:
                    caps[name] = self._add_config_cap(name)

        # finished
        return caps

    def _add_config_cap(self, name: str) -> Tuple[bool, bool, bool]:
        """Check for getter and setter

        Params:
            name: Name of variable.

        Returns:
            Tuple of booleans indication whether getter, setter and get_options exist.
        """
        return (
            hasattr(self, "_get_config_" + name),
            hasattr(self, "_set_config_" + name),
            hasattr(self, "_get_config_options_" + name),
        )

    async def get_config_caps(self, **kwargs: Any) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns dict of all config capabilities. First value is whether it has a getter, second is for the setter,
        third is for a list of possible options..

        Returns:
            Dict with config caps
        """
        return self._config_caps

    async def get_config_value(self, name: str, **kwargs: Any) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError: If config item of given name does not exist.
        """

        # valid parameter?
        if name not in self._config_caps:
            raise ValueError("Invalid parameter %s" % name)
        if not self._config_caps[name][0]:
            raise ValueError("Parameter %s is not remotely accessible.")

        # get getter method and call it
        getter = getattr(self, "_get_config_" + name)
        return await getter()

    async def get_config_value_options(self, name: str, **kwargs: Any) -> List[str]:
        """Returns possible values for config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Possible values.

        Raises:
            ValueError: If config item of given name does not exist.
        """

        # valid parameter?
        if name not in self._config_caps:
            raise ValueError("Invalid parameter %s" % name)
        if not self._config_caps[name][2]:
            raise ValueError("Parameter %s has no list of possible values.")

        # get getter method and call it
        options = getattr(self, "_get_config_options_" + name)
        return cast(List[str], await options())

    async def set_config_value(self, name: str, value: Any, **kwargs: Any) -> None:
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """

        # valid parameter?
        if name not in self._config_caps:
            raise ValueError("Invalid parameter %s" % name)
        if not self._config_caps[name][1]:
            raise ValueError("Parameter %s is not remotely settable.")

        # get setter and call it
        setter = getattr(self, "_set_config_" + name)
        await setter(value)

    async def set_state(self, state: ModuleState, error_string: Optional[str] = None) -> None:
        """Set state of module.

        Args:
            state: New state to set.
            error_string: If given, set error string.
        """

        # log?
        if state != self._state:
            log.info("Set module state to %s.", state)

        # set it
        self._state = state
        if error_string is not None:
            self.set_error_string(error_string)

    async def get_state(self, **kwargs: Any) -> ModuleState:
        """Returns current state of module."""
        return self._state

    async def reset_error(self, **kwargs: Any) -> bool:
        """Reset error of module, if any. Should be overwritten by derived class to handle error resolution."""
        self._state = ModuleState.READY
        self.set_error_string()
        return True

    async def _default_remote_error_callback(self, exception: exc.PyObsError) -> None:
        """Called on severe errors.

        Args:
            exception: Exception that caused severe error.
        """

        # set error string
        if isinstance(exception, exc.RemoteError):
            error = f"Servere error in {exception.module} module: {exception}"
        else:
            error = f"Severe error: {exception}"
        self.set_error_string(error)

        # log it and set state
        log.critical(error)
        await self.set_state(ModuleState.ERROR)

    def set_error_string(self, error: str = "") -> None:
        """Set error string."""
        self._error_string = error

    async def get_error_string(self, **kwargs: Any) -> str:
        """Returns description of error, if any."""
        return self._error_string


class MultiModule(Module):
    """Wrapper for running multiple modules in a single process."""

    __module__ = "pyobs.modules"

    def __init__(
        self,
        modules: Dict[str, Union[Module, Dict[str, Any]]],
        shared: Optional[Dict[str, Union[object, Dict[str, Any]]]] = None,
        **kwargs: Any,
    ):
        """
        Args:
            modules: Dictionary with modules.
            shared: Shared objects between modules.
        """
        Module.__init__(self, name="multi", **kwargs)

        # create shared objects
        self._shared: Dict[str, Module] = {}
        if shared:
            for name, obj in shared.items():
                # if obj is an object definition, create it, otherwise just set it
                self._shared[name] = self.add_child_object(obj)

        # create modules
        self._modules = {}
        for name, mod in modules.items():
            # what is it?
            if isinstance(mod, Module):
                # it's a module already, store it
                self._modules[name] = mod
            elif isinstance(mod, dict):
                # dictionary, create it
                self._modules[name] = self.add_child_object(mod, **self._shared, copy_comm=False)

    @property
    def modules(self) -> Dict[str, Module]:
        return self._modules

    def __contains__(self, name: str) -> bool:
        """Checks, whether this multi-module contains a module of given name."""
        return name in self._modules

    def __getitem__(self, name: str) -> Module:
        """Returns module of given name."""
        return self._modules[name]


__all__ = ["Module", "MultiModule", "timeout"]
