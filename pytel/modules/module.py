import inspect
import logging
import threading
import time
from typing import Union, Type
from py_expression_eval import Parser

from pytel.application import APP


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


class PytelModule:
    def __init__(self, name=None, comm=None, environment=None, db=None, thread_funcs=None,
                 restart_threads=True, *args, **kwargs):

        # an event that will be fired when closing the module
        self.closing = threading.Event()

        # name
        self._name = name

        # get list of client interfaces
        self._interfaces = []
        self._methods = {}
        self._get_interfaces_and_methods()

        # some linked object
        self._comm = comm
        self._environment = environment
        self._db = db

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
            self._threads = {threading.Thread(target=PytelModule._thread_func, name=t.__name__, args=(t,)): t
                             for t in thread_funcs}
            self._watchdog = threading.Thread(target=self._watchdog_func, name='watchdog')

    @property
    def comm(self):
        return self._comm

    def proxy(self, name_or_object: Union[str, 'PytelModule'], obj_type: Type['PytelModule']) -> 'PytelModule':
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

    @property
    def environment(self):
        return self._environment

    @property
    def db(self):
        return self._db

    @staticmethod
    def _thread_func(target):
        try:
            target()
        except:
            log.exception('Exception in thread method %s.' % target.__name__)

    def open(self) -> bool:
        # start threads and watchdog
        for thread, target in self._threads.items():
            log.info('Starting thread for %s...', target.__name__)
            thread.start()
        if self._watchdog:
            self._watchdog.start()

        # success
        self._opened = True
        return True

    @property
    def opened(self):
        return self._opened

    def close(self):
        # request closing of object (used for long-running methods)
        self.closing.set()

        # join watchdog and then all threads
        if self._watchdog and self._watchdog.is_alive():
            self._watchdog.join()
        [t.join() for t in self._threads.keys() if t.is_alive()]

    def _watchdog_func(self):
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

    @property
    def name(self):
        return self._name

    def implements(self, interface):
        """checks, whether this object implements a given interface"""
        return interface.implemented_by(self)

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def methods(self):
        return self._methods

    def _get_interfaces_and_methods(self):
        import pytel.interfaces

        # get interfaces
        self._interfaces = []
        self._methods = {}
        for _, interface in inspect.getmembers(pytel.interfaces, predicate=inspect.isclass):
            # is module a sub-class of that class that inherits from Interface?
            if isinstance(self, interface) and issubclass(interface, pytel.interfaces.Interface):
                # we ignore the interface "Interface"
                if interface == pytel.interfaces.Interface:
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

        # remove interfaces that are implemented by others
        """
        to_delete = []
        for i1 in self._interfaces:
            for i2 in self._interfaces:
                if i1 != i2 and issubclass(i1, i2):
                    # i1 implements i2, so remove i2
                    to_delete.append(i2)
        for d in list(set(to_delete)):
            self._interfaces.remove(d)
        """

    def _sleep_long(self, sec):
        while sec > 0:
            time.sleep(1)
            sec -= 1
            self.check_running()

    def quit(self):
        if APP():
            APP().quit()
        else:
            log.error('No app given, cannot quit.')

    def open_file(self, filename: str, mode: str, compression: bool = None):
        """Open a file. The handling class is chosen depending on the vfs root in the filename.

        Args:
            filename (str): Name of file to open.
            mode (str): Opening mode.
            compression (bool): Automatically (de)compress data if True. Automatically determine from filename if None.

        Returns:
            (BaseFile) File object for given file.
        """
        if APP() and APP().vfs:
            return APP().vfs.open_file(filename, mode, compression)
        else:
            log.error('Trying to open file, but no VFS provided in config...')
            return None


__all__ = ['PytelModule', 'timeout']
