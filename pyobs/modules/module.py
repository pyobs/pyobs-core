import asyncio
import inspect
import logging
from typing import Union, Type, Any, Callable, Dict, Tuple, List, TypeVar, Optional, cast
from py_expression_eval import Parser

from pyobs.events import ModuleOpenedEvent, Event
from pyobs.object import Object
from pyobs.interfaces import IModule, IConfig, Interface
from pyobs.utils.types import cast_response_to_simple, cast_bound_arguments_to_real
from pyobs.version import version, version_tuple

log = logging.getLogger(__name__)


F = TypeVar('F', bound=Callable[..., Any])


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
            to = 0.

            # do we have a timeout?
            if func_timeout is not None:
                # what is it?
                if callable(func_timeout):
                    # this is a method, does it have a timeout on it's own? then use it
                    try:
                        if hasattr(func_timeout, 'timeout'):
                            # call timeout method, only works if this has the same parameters
                            to = await getattr(func_timeout, 'timeout')(obj, *args, **kwargs)
                        else:
                            # call method directly
                            to = await func_timeout(obj, *args, **kwargs)
                    except:
                        log.exception('Could not call timeout method.')

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
                        log.exception('Could not convert timeout to float.')
                        to = 0.

            # return it
            return to

        # decorate method
        setattr(func, 'timeout', _timeout)
        return func

    return timeout_decorator


class Module(Object, IModule, IConfig):
    """Base class for all pyobs modules."""
    __module__ = 'pyobs.modules'

    def __init__(self, name: Optional[str] = None, label: Optional[str] = None, **kwargs: Any):
        """
        Args:
            name: Name of module. If None, ID from comm object is used.
            label: Label for module. If None, name is used.
        """
        Object.__init__(self, **kwargs)

        # get list of client interfaces
        self._interfaces: List[Type[Interface]] = []
        self._methods: Dict[str, Tuple[Callable[..., Any], inspect.Signature]] = {}
        self._get_interfaces_and_methods()

        # get configuration caps, i.e. all parameters from c'tor
        self._config_caps = self._get_config_caps()

        # name and label
        self._device_name = name if name is not None else self.comm.name
        self._label = label if label is not None else self._device_name

    async def open(self) -> None:
        # open comm
        if self.comm is not None:
            # open it and connect module
            await self.comm.open()
            self.comm.module = self

            # react to connecting modules
            await self.comm.register_event(ModuleOpenedEvent, self._on_module_opened)

        """Open module."""
        await Object.open(self)

    async def close(self) -> None:
        """Close module."""
        await Object.close(self)

        # close comm
        if self.comm is not None:
            log.info('Closing connection to server...')
            await self.comm.close()

    async def main(self) -> None:
        """Main loop for application."""
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                return

    def name(self, **kwargs: Any) -> str:
        """Returns name of module."""
        return '' if self._device_name is None else self._device_name

    async def get_label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        return '' if self._label is None else self._label

    async def get_version(self, **kwargs: Any) -> str:
        """Returns pyobs version of module."""
        return version()

    async def _on_module_opened(self, event: Event, sender: str) -> bool:
        """React to other modules connecting."""
        if sender == self.comm.name or not isinstance(event, ModuleOpenedEvent):
            return False

        # get proxy and version
        proxy = await self.proxy(sender, IModule)
        module_version = await proxy.get_version()
        my_version = version()

        # log it
        log.debug(f'Other module {sender} found, running on pyobs {module_version}.')

        # check minor and major version, ignore patch level
        v1, v2 = version_tuple(my_version), version_tuple(module_version)
        if v1[:2] != v2[:2]:
            if v1 > v2:
                log.error(f'Found module "{sender}" with older pyobs version {module_version} (<{my_version}), '
                          f'please update it.')
            else:
                log.error(f'Found module "{sender}" with newer pyobs version {module_version} (>{my_version}), '
                          f'please update this module.')

        # okay
        return True

    @property
    def interfaces(self) -> List[Type[Interface]]:
        """List of implemented interfaces."""
        return self._interfaces

    @property
    def methods(self) -> Dict[str, Tuple[Callable[..., Any], inspect.Signature]]:
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

                    # fill dict of name->(method, signature)
                    self._methods[method_name] = (func, signature)

    def quit(self) -> None:
        """Quit module."""
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

        # get method and signature (may raise KeyError)
        func, signature = self.methods[method]

        # bind parameters
        ba = signature.bind(*args, **kwargs)
        ba.apply_defaults()

        # cast to types requested by method
        cast_bound_arguments_to_real(ba, signature)

        # get additional args and kwargs and delete from ba
        func_args = []
        func_kwargs = {}
        if 'args' in ba.arguments:
            func_args = ba.arguments['args']
            del ba.arguments['args']
        if 'kwargs' in ba.arguments:
            func_kwargs = ba.arguments['kwargs']
            del ba.arguments['kwargs']

        # call method
        response = await func(*func_args, **ba.arguments, **func_kwargs)

        # finished
        return cast_response_to_simple(response)

    def _get_config_caps(self) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns a dictionary with config caps."""

        # init dict of caps and types
        caps = {}

        # loop super classes
        for cls in inspect.getmro(self.__class__):
            # ignore Object and Module
            if cls in [Object, Module]:
                continue

            # get signature
            sig = inspect.signature(getattr(cls, '__init__'))
            for name in sig.parameters:
                # ignore self, args, kwargs
                if name in ['self', 'args', 'kwargs']:
                    continue

                # check for getter and setter
                caps[name] = (hasattr(self, '_get_config_' + name),
                              hasattr(self, '_set_config_' + name),
                              hasattr(self, '_get_config_options_' + name))

        # finished
        return caps

    def get_config_caps(self, **kwargs: Any) -> Dict[str, Tuple[bool, bool, bool]]:
        """Returns dict of all config capabilities. First value is whether it has a getter, second is for the setter,
        third is for a list of possible options..

        Returns:
            Dict with config caps
        """
        return self._config_caps

    def get_config_value(self, name: str, **kwargs: Any) -> Any:
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
            raise ValueError('Invalid parameter %s' % name)
        if not self._config_caps[name][0]:
            raise ValueError('Parameter %s is not remotely accessible.')

        # get getter method and call it
        getter = getattr(self, '_get_config_' + name)
        return getter()

    def get_config_value_options(self, name: str, **kwargs: Any) -> List[str]:
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
            raise ValueError('Invalid parameter %s' % name)
        if not self._config_caps[name][2]:
            raise ValueError('Parameter %s has no list of possible values.')

        # get getter method and call it
        options = getattr(self, '_get_config_options_' + name)
        return cast(List[str], options())

    def set_config_value(self, name: str, value: Any, **kwargs: Any) -> None:
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """

        # valid parameter?
        if name not in self._config_caps:
            raise ValueError('Invalid parameter %s' % name)
        if not self._config_caps[name][1]:
            raise ValueError('Parameter %s is not remotely settable.')

        # get setter and call it
        setter = getattr(self, '_set_config_' + name)
        setter(value)


class MultiModule(Module):
    """Wrapper for running multiple modules in a single process."""
    __module__ = 'pyobs.modules'

    def __init__(self, modules: Dict[str, Union[Module, Dict[str, Any]]],
                 shared: Optional[Dict[str, Union[object, Dict[str, Any]]]] = None,
                 **kwargs: Any):
        """
        Args:
            modules: Dictionary with modules.
            shared: Shared objects between modules.
        """
        Module.__init__(self, name='multi', **kwargs)

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


__all__ = ['Module', 'MultiModule', 'timeout']
