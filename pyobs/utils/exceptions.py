from __future__ import annotations

from typing import Optional, List, NamedTuple, Any, Tuple, Type, Dict, Callable
import time


class PyObsException:
    """Base class for all exceptions"""

    def __init__(self, message: Optional[str] = None):
        self.message = message


class _Meta(type):
    """Metaclass for defining exceptions."""

    def __call__(cls, *args: Any, **kwargs: Any) -> PyObsException:
        """Called when you call MyNewClass()"""
        obj: PyObsException = type.__call__(cls, *args, **kwargs)
        handle_exception(obj)
        return obj


#######################################


class MotionError(PyObsException, metaclass=_Meta):
    pass


class CannotInitError(MotionError, metaclass=_Meta):
    pass


class CannotParkError(MotionError, metaclass=_Meta):
    pass


class CannotMoveError(MotionError, metaclass=_Meta):
    pass


#######################################


class RemoteException(PyObsException, metaclass=_Meta):
    """Remote exception encapsulating basic exception from other module"""

    def __init__(
        self, message: Optional[str] = None, module: Optional[str] = None, exception: Optional[PyObsException] = None
    ):
        PyObsException.__init__(self, message)
        self.module = module
        self.exception = exception


class SevereException(PyObsException):
    """Severe exception that is raised after multiple raised other exceptions."""

    def __init__(
        self, message: Optional[str] = None, module: Optional[str] = None, exception: Optional[PyObsException] = None
    ):
        PyObsException.__init__(self, message)
        self.module = module
        self.exception = exception


class LoggedException(NamedTuple):
    time: float
    exception: PyObsException


class ExceptionHandler(NamedTuple):
    exc_type: Type[PyObsException]
    limit: int
    timespan: Optional[float] = None
    module: Optional[str] = None
    callback: Optional[Callable[[Type[PyObsException], Optional[str]], None]] = None
    throw: bool = True


#######################################


local_exceptions: Dict[Type[PyObsException], List[LoggedException]] = {}
remote_exceptions: Dict[Tuple[Type[PyObsException], str], List[LoggedException]] = {}
handlers: List[ExceptionHandler] = []


def register_exception(
    exc_type: Type[PyObsException],
    limit: int,
    timespan: Optional[float] = None,
    module: Optional[str] = None,
    callback: Optional[Callable[[Type[PyObsException], Optional[str]], None]] = None,
    throw: bool = True,
) -> None:
    handlers.append(ExceptionHandler(exc_type, limit, timespan, module, callback, throw))


def handle_exception(exception: PyObsException) -> None:
    # get module and store exception
    module = exception.module if isinstance(exception, RemoteException) else None

    # store exception itself
    _store_exception(exception, module)

    # if there is a child exception, store it as well
    if hasattr(exception, "exception"):
        _store_exception(getattr(exception, "exception"), module)

    # now check, whether something is severe
    _check_severity()


def _store_exception(exception: PyObsException, module: Optional[str]) -> None:
    # get all classes from mro
    for e in type(exception).__mro__:
        # only pyobs exceptions
        if not issubclass(e, PyObsException):
            continue

        # log
        le = LoggedException(time=time.time(), exception=exception)

        # store it
        if module is None:
            # add to local exceptions
            if e not in local_exceptions:
                local_exceptions[e] = []
            local_exceptions[e].append(le)

        else:
            # add to remote exceptions
            if (e, module) not in remote_exceptions:
                remote_exceptions[e, module] = []
            remote_exceptions[e, module].append(le)


def _check_severity() -> None:
    # loop all handlers
    for h in handlers:
        # get all exceptions that this handler deals with
        exceptions = []
        if h.module is None:
            # add local exceptions
            if h.exc_type in local_exceptions:
                exceptions.extend(local_exceptions[h.exc_type])
        else:
            # add remote exceptions
            if (h.exc_type, h.module) in remote_exceptions:
                exceptions.extend(remote_exceptions[h.exc_type, h.module])

        # got a timespan?
        if h.timespan is None:
            # count all
            count = len(exceptions)

        else:
            # count all within timespan
            earliest = time.time() - h.timespan
            count = len(list(filter(lambda le: le.time >= earliest, exceptions)))

        # more than limit?
        if count >= h.limit:
            # callback?
            if h.callback is not None:
                h.callback(h.exc_type, h.module)


#######################################


def cb(exc: Type[PyObsException], module: Optional[str] = None) -> None:
    print("callback", module, exc)


register_exception(MotionError, limit=3, timespan=2, callback=cb)

RemoteException(message="Hello world", module="telescope", exception=CannotInitError())
CannotParkError()
time.sleep(1)
CannotInitError()

# import pprint
# pprint.pprint(local_exceptions)
