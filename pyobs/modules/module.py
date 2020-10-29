from __future__ import annotations
import datetime
import inspect
import logging
import threading
from typing import Union, Type, Any, Callable, Dict
from py_expression_eval import Parser
from astropy.coordinates import EarthLocation
from astroplan import Observer
import pytz
from pyobs.comm.dummy import DummyComm

from pyobs.environment import Environment
from pyobs.comm import Comm
from pyobs.interfaces import IModule
from pyobs.object import get_object, create_object
from pyobs.vfs import VirtualFileSystem
from pyobs.utils.types import cast_response_to_simple, cast_bound_arguments_to_real

log = logging.getLogger(__name__)


def timeout(func_timeout: Union[str, int, Callable, None] = None):
    """Decorates a method with information about timeout for an async HTTP call.

    :param func_timeout:  Integer or string that specifies the timeout.
                          If string, it is parsed using the variables in kwargs.
    """

    def timeout_decorator(func):
        def _timeout(*args, **kwargs):
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
                            to = func_timeout.timeout(*args, **kwargs)
                        else:
                            # call method directly
                            to = func_timeout(*args, **kwargs)
                    except:
                        log.error('Could not call timeout method.')

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


class Module(IModule):
    """Base class for all pyobs modules."""

    def __init__(self, name: str = None, label: str = None, comm: Union[Comm, dict] = None,
                 vfs: Union[VirtualFileSystem, dict] = None, timezone: Union[str, datetime.tzinfo] = 'utc',
                 location: Union[str, dict, EarthLocation] = None, *args, **kwargs):
        """Initializes a new pyobs module.

        Args:
            name: Name of module. If None, ID from comm object is used.
            label: Label for module. If None, name is used.
            comm: Comm object to use
            vfs: VFS to use (either object or config)
            timezone: Timezone at observatory.
            location: Location of observatory, either a name or a dict containing latitude, longitude, and elevation.
        """

        # an event that will be fired when closing the module
        self.closing = threading.Event()

        # get list of client interfaces
        self._interfaces = []
        self._methods = {}
        self._get_interfaces_and_methods()

        # closing event
        self.closing = threading.Event()

        # sub modules
        self._sub_modules = []

        # comm object
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
        self._name = name
        if self._name is None:
            self._name = self.comm.name
        self._label = label
        if self._label is None:
            self._label = self._name

        # create vfs
        if vfs:
            self.vfs = get_object(vfs)
        else:
            from pyobs.vfs import VirtualFileSystem
            self.vfs = VirtualFileSystem()

        # timezone
        if isinstance(timezone, datetime.tzinfo):
            self.timezone = timezone
        elif isinstance(timezone, str):
            self.timezone = pytz.timezone(timezone)
        else:
            raise ValueError('Unknown format for timezone.')
        log.info('Using timezone %s.', timezone)

        # location
        if location is None:
            self.location = None
        elif isinstance(location, EarthLocation):
            self.location = location
        elif isinstance(location, str):
            self.location = EarthLocation.of_site(location)
        elif isinstance(location, dict):
            self.location = EarthLocation.from_geodetic(location['longitude'], location['latitude'],
                                                        location['elevation'])
        else:
            raise ValueError('Unknown format for location.')

        # create observer
        self.observer = None
        if self.location is not None:
            log.info('Setting location to longitude=%s, latitude=%s, and elevation=%s.',
                     self.location.lon, self.location.lat, self.location.height)
            self.observer = Observer(location=self.location, timezone=timezone)

        # opened?
        self._opened = False

        # thread function(s)
        self._threads = {}
        self._watchdog = threading.Thread(target=self._watchdog_func, name='watchdog')

    def _add_thread_func(self, func: Callable, restart: bool = True):
        """Add a new thread func.

        MUST be called in constructor of derived class or at least before calling open() on the module.

        Args:
            func: Func to add.
            restart: Whether to restart this function.
        """

        # create thread
        t = threading.Thread(target=Module._thread_func, name=func.__name__, args=(func,))

        # add it
        self._threads[t] = (func, restart)

    def open(self):
        """Open module."""

        # open comm
        if self.comm is not None:
            # open it and connect module
            self.comm.open()
            self.comm.module = self

        # start threads and watchdog
        for thread, (target, _) in self._threads.items():
            log.info('Starting thread for %s...', target.__name__)
            thread.start()
        if self._watchdog:
            self._watchdog.start()

        # open sub modules
        for mod in self._sub_modules:
            if hasattr(mod, 'open'):
                mod.open()

        # success
        self._opened = True

    @property
    def opened(self):
        return self._opened

    def close(self):
        """Close module."""

        # request closing of object (used for long-running methods)
        self.closing.set()

        # close sub modules
        for mod in self._sub_modules:
            if hasattr(mod, 'close'):
                mod.close()

        # join watchdog and then all threads
        if self._watchdog and self._watchdog.is_alive():
            self._watchdog.join()
        [t.join() for t in self._threads.keys() if t.is_alive()]

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

    @staticmethod
    def _thread_func(target):
        """Run given function.

        Args:
            target: Function to run.
        """
        try:
            target()
        except:
            log.exception('Exception in thread method %s.' % target.__name__)

    def _watchdog_func(self):
        """Watchdog thread that tries to restart threads if they quit."""

        while not self.closing.is_set():
            # get dead threads that need to be restarted
            dead = {}
            for thread, (target, restart) in self._threads.items():
                if not thread.is_alive():
                    dead[thread] = (target, restart)

            # restart dead threads or quit
            for thread, (target, restart) in dead.items():
                if restart:
                    log.error('Thread for %s has died, restarting...', target.__name__)
                    del self._threads[thread]
                    thread = threading.Thread(target=target, name=target.__name__)
                    thread.start()
                    self._threads[thread] = target
                else:
                    log.error('Thread for %s has died, quitting...', target.__name__)
                    self.quit()
                    return

            # sleep a little
            self.closing.wait(1)

    def check_running(self):
        """Check, whether an object should be closing. Can be polled by long-running methods.

        Raises:
            InterruptedError: Raised when object should be closing.
        """
        if self.closing.is_set():
            raise InterruptedError
        return True

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

    def open_file(self, filename: str, mode: str, compression: bool = None):
        """Open a file. The handling class is chosen depending on the vfs root in the filename.

        Args:
            filename (str): Name of file to open.
            mode (str): Opening mode.
            compression (bool): Automatically (de)compress data if True. Automatically determine from filename if None.

        Returns:
            (BaseFile) File object for given file.
        """
        return self.vfs.open_file(filename, mode, compression)

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

        try:
            # call method
            response = func(*func_args, **ba.arguments, **func_kwargs)

            # finished
            return cast_response_to_simple(response)
        except Exception as e:
            log.exception('Error on remote procedure call: %s' % str(e))

    def _create_sub_module(self, config: dict, **kwargs) -> Module:
        """Create a new sub-module, which will automatically be opened and closed.

        Args:
            config: Module definition

        Returns:
            The created module.
        """

        # create it
        module = create_object(config, timezone=self.timezone, location=self.location, **kwargs)

        # add to list
        self._sub_modules.append(module)

        # return it
        return module


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
        self._shared = {}
        if shared:
            for name, obj in shared.items():
                # if obj is an object definition, create it, otherwise just set it
                self._shared[name] = self._create_sub_module(obj) if isinstance(obj, dict) and 'class' in obj else obj

        # create modules
        self._modules = {}
        for name, mod in modules.items():
            # what is it?
            if isinstance(mod, Module):
                # it's a module already, store it
                self._modules[name] = mod
            elif isinstance(mod, dict):
                # dictionary, create it
                self._modules[name] = self._create_sub_module(mod, **self._shared)

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
