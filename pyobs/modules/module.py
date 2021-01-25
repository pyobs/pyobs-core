import inspect
import logging
from typing import Union, Type, Any, Callable, Dict, Tuple, List
from py_expression_eval import Parser

from pyobs.comm.dummy import DummyComm
from pyobs.object import Object
from pyobs.comm import Comm
from pyobs.interfaces import IModule, IConfig
from pyobs.object import get_object
from pyobs.utils.types import cast_response_to_simple, cast_bound_arguments_to_real

log = logging.getLogger(__name__)


def timeout(func_timeout: Union[str, int, Callable, None] = None):
    """Decorates a method with information about timeout for an async HTTP call.

    :param func_timeout:  Integer or string that specifies the timeout.
                          If string, it is parsed using the variables in kwargs.
    """

    def timeout_decorator(func):
        def _timeout(obj, *args, **kwargs):
            # define variables as non-local
            nonlocal func_timeout, func

            # init to 0 second
            to = 0

            # do we have a timeout?
            if func_timeout is not None:
                # what is it?
                if callable(func_timeout):
                    # this is a method, does it have a timeout on it's own? then use it
                    try:
                        if hasattr(func_timeout, 'timeout'):
                            # call timeout method, only works if this has the same parameters
                            to = func_timeout.timeout(obj, *args, **kwargs)
                        else:
                            # call method directly
                            to = func_timeout(obj, *args, **kwargs)
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
                        to = 0

            # return it
            return to

        # decorate method
        setattr(func, 'timeout', _timeout)
        return func

    return timeout_decorator


class Module(Object, IModule, IConfig):
    """Base class for all pyobs modules."""

    def __init__(self, name: str = None, label: str = None, comm: Union[Comm, dict] = None, *args, **kwargs):
        """Initializes a new pyobs module.

        Args:
            name: Name of module. If None, ID from comm object is used.
            label: Label for module. If None, name is used.
            comm: Comm object to use
        """
        Object.__init__(self, *args, **kwargs)

        # get list of client interfaces
        self._interfaces: List[Type] = []
        self._methods: Dict[str, Tuple[Callable, inspect.Signature]] = {}
        self._get_interfaces_and_methods()

        # get configuration options, i.e. all parameters from c'tor
        self._config_options = self._get_config_options()

        # comm object
        self.comm: Comm
        if comm is None:
            self.comm = DummyComm()
        elif isinstance(comm, Comm):
            self.comm = comm
        elif isinstance(comm, dict):
            log.info('Creating comm object...')
            self.comm = get_object(comm)
        else:
            raise ValueError('Invalid Comm object')

        # name and label
        self._name: str = name if name is not None else self.comm.name
        self._label: str = label if label is not None else self._name

    def open(self):
        """Open module."""
        Object.open(self)

        # open comm
        if self.comm is not None:
            # open it and connect module
            self.comm.open()
            self.comm.module = self

    def close(self):
        """Close module."""
        Object.close(self)

        # close comm
        if self.comm is not None:
            log.info('Closing connection to server...')
            self.comm.close()

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
        return self.comm.proxy(name_or_object, obj_type)

    def main(self):
        """Main loop for application."""
        while not self.closing.is_set():
            self.closing.wait(1)

    def name(self, *args, **kwargs) -> str:
        """Returns name of module."""
        return self._name

    def label(self, *args, **kwargs) -> str:
        """Returns label of module."""
        return self._label

    def implements(self, interface):
        """checks, whether this object implements a given interface"""
        return interface.implemented_by(self)

    @property
    def interfaces(self):
        """List of implemented interfaces."""
        return self._interfaces

    @property
    def methods(self):
        """List of methods."""
        return self._methods

    def _get_interfaces_and_methods(self):
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

    def quit(self):
        """Quit module."""
        self.closing.set()

    def execute(self, method, *args, **kwargs) -> Any:
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
        func_args = ba.arguments['args']
        func_kwargs = ba.arguments['kwargs']
        del ba.arguments['args']
        del ba.arguments['kwargs']

        # call method
        response = func(*func_args, **ba.arguments, **func_kwargs)

        # finished
        return cast_response_to_simple(response)

    def _get_config_options(self) -> dict:
        """Returns a dictionary with config options."""

        # init dict of options and types
        opts = {}

        # loop super classes
        for cls in inspect.getmro(self.__class__):
            # ignore Object and Module
            if cls in [Object, Module]:
                continue

            # get signature
            sig = inspect.signature(cls.__init__)
            for name in sig.parameters:
                # ignore self, args, kwargs
                if name in ['self', 'args', 'kwargs']:
                    continue

                # check for getter and setter
                getter = hasattr(self, '_get_config_' + name)
                setter = hasattr(self, '_set_config_' + name)
                opts[name] = (getter, setter)

        # finished
        return opts

    def get_config_options(self, *args, **kwargs) -> Dict[str, Tuple[bool, bool]]:
        """Returns dict of all config options. First value is whether it has a getter, second is for the setter.

        Returns:
            Dict with config options
        """
        return self._config_options

    def get_config_value(self, name: str, *args, **kwargs) -> Any:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError if config item of given name does not exist.
        """

        # valid parameter?
        if name not in self._config_options:
            raise ValueError('Invalid parameter %s' % name)
        if not self._config_options[name][0]:
            raise ValueError('Parameter %s is not remotely accessible.')

        # get getter method and call it
        getter = getattr(self, '_get_config_' + name)
        return getter()

    def set_config_value(self, name: str, value: Any, *args, **kwargs):
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError if config item of given name does not exist or value is invalid.
        """

        # valid parameter?
        if name not in self._config_options:
            raise ValueError('Invalid parameter %s' % name)
        if not self._config_options[name][1]:
            raise ValueError('Parameter %s is not remotely settable.')

        # get setter and call it
        setter = getattr(self, '_set_config_' + name)
        setter(value)


class MultiModule(Module):
    """Wrapper for running multiple modules in a single process."""

    def __init__(self, modules: Dict[str, Union[Module, dict]], shared: Dict[str, Union[object, dict]] = None,
                 *args, **kwargs):
        """Initializes a new pyobs multi module.

        Args:
            modules: Dictionary with modules.
            shared: Shared objects between modules.
        """
        Module.__init__(self, name='multi', *args, **kwargs)

        # create shared objects
        self._shared: Dict[str, Module] = {}
        if shared:
            for name, obj in shared.items():
                # if obj is an object definition, create it, otherwise just set it
                self._shared[name] = self._add_child_object(obj)

        # create modules
        self._modules = {}
        for name, mod in modules.items():
            # what is it?
            if isinstance(mod, Module):
                # it's a module already, store it
                self._modules[name] = mod
            elif isinstance(mod, dict):
                # dictionary, create it
                self._modules[name] = self._add_child_object(mod, **self._shared)

    @property
    def modules(self):
        return self._modules

    def __contains__(self, name: str) -> bool:
        """Checks, whether this multi-module contains a module of given name."""
        return name in self._modules

    def __getitem__(self, name: str) -> Module:
        """Returns module of given name."""
        return self._modules[name]


__all__ = ['Module', 'MultiModule', 'timeout']
