import inspect
import logging
import threading
from typing import Union, Type, Any, Callable
from py_expression_eval import Parser
from astropy.coordinates import EarthLocation
from astroplan import Observer
import pytz

from pyobs.environment import Environment
from pyobs.comm import Comm
from pyobs.object import get_object
from pyobs.vfs import VirtualFileSystem
from pyobs.utils.types import cast_response_to_simple, cast_bound_arguments_to_real

log = logging.getLogger(__name__)


def timeout(func_timeout: Union[str, int, None] = None):
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
                # is it a string?
                if isinstance(func_timeout, str):
                    # evaluate
                    try:
                        parser = Parser()
                        to = parser.parse(func_timeout).evaluate(kwargs)
                    except Exception:
                        log.error('Could not find timeout "%s" in list of parameters.', func_timeout)
                else:
                    # add timeout directly
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


class PyObsModule:
    """Base class for all pyobs modules."""

    def __init__(self, name: str = None, comm: Union[Comm, dict] = None, vfs: Union[VirtualFileSystem, dict] = None,
                 timezone: str = 'utc', location: Union[str, dict] = None,
                 plugins: list = None, thread_funcs: [list, Callable] = None,
                 restart_threads: bool = True, *args, **kwargs):
        """Initializes a new pyobs module.

        Args:
            name: Name of module.
            comm: Comm object to use
            vfs: VFS to use (either object or config)
            timezone: Timezone at observatory.
            location: Location of observatory, either a name or a dict containing latitude, longitude, and elevation.
            plugins: List of plugins to start.
            thread_funcs: Functions to start in a separate thread.
            restart_threads: Whether to automatically restart threads when they quit.
        """

        # an event that will be fired when closing the module
        self.closing = threading.Event()

        # name
        self._name = name

        # get list of client interfaces
        self._interfaces = []
        self._methods = {}
        self._get_interfaces_and_methods()

        # closing event
        self.closing = threading.Event()

        # connect comm module
        self.comm = comm
        if comm:
            self.comm.module = self

        # create vfs
        if vfs:
            self.vfs = get_object(vfs)
        else:
            from pyobs.vfs import VirtualFileSystem
            self.vfs = VirtualFileSystem()

        # timezone
        self.timezone = pytz.timezone(timezone)
        log.info('Using timezone %s.', timezone)

        # location
        if location is None:
            self.location = None
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

        # plugins
        self._plugins = []
        if plugins:
            for cfg in plugins.values():
                plg = get_object(cfg)   # Type: PyObsModule
                plg.comm = self.comm
                plg.observer = self.observer
                self._plugins.append(plg)

        # opened?
        self._opened = False

        # thread function(s)
        self._restart_threads = restart_threads
        self._threads = {}
        self._watchdog = None
        if thread_funcs:
            # we want a list
            if not hasattr(thread_funcs, '__iter__'):
                thread_funcs = [thread_funcs]

            # create threads and watchdog
            self._threads = {threading.Thread(target=PyObsModule._thread_func, name=t.__name__, args=(t,)): t
                             for t in thread_funcs}
            self._watchdog = threading.Thread(target=self._watchdog_func, name='watchdog')

    def open(self):
        """Open module."""

        # open plugins
        if self._plugins:
            log.info('Opening plugins...')
            for plg in self._plugins:
                plg.open()

        # start threads and watchdog
        for thread, target in self._threads.items():
            log.info('Starting thread for %s...', target.__name__)
            thread.start()
        if self._watchdog:
            self._watchdog.start()

        # success
        self._opened = True

    @property
    def opened(self):
        return self._opened

    def close(self):
        """Close module."""

        # request closing of object (used for long-running methods)
        self.closing.set()

        # join watchdog and then all threads
        if self._watchdog and self._watchdog.is_alive():
            self._watchdog.join()
        [t.join() for t in self._threads.keys() if t.is_alive()]

        # close plugins
        if self._plugins:
            log.info('Closing plugins...')
            for plg in self._plugins:
                plg.close()

    def proxy(self, name_or_object: Union[str, object], obj_type: Type):
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

        if isinstance(name_or_object, obj_type):
            # return directly
            return name_or_object

        elif isinstance(name_or_object, str):
            # get proxy
            proxy = self.comm[name_or_object]

            # check it
            if proxy is None:
                raise ValueError('Could not create proxy for given name "%s".' % name_or_object)
            elif isinstance(proxy, obj_type):
                return proxy
            else:
                raise ValueError('Proxy obtained from given name "%s" is not of requested type "%s".' %
                                 (name_or_object, obj_type))

        else:
            # completely wrong...
            raise ValueError('Given parameter is neither a name nor an object of requested type "%s".' % obj_type)

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
            # get dead threads
            dead = {thread: target for thread, target in self._threads.items() if not thread.is_alive()}

            # restart dead threads or quit
            for thread, target in dead.items():
                if self._restart_threads:
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

    def run(self):
        """Main loop for application."""
        while not self.closing.is_set():
            self.closing.wait(1)

    @property
    def name(self):
        """Name of module."""
        return self._name

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

        try:
            # call method
            response = func(**ba.arguments)

            # finished
            return cast_response_to_simple(response)
        except Exception as e:
            log.exception('Error on remote procedure call: %s' % str(e))


__all__ = ['PyObsModule', 'timeout']
