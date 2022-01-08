from __future__ import annotations

from typing import Optional, List, NamedTuple, Any, Tuple, Type, Dict, Callable
import time


class PyObsException(Exception):
    """Base class for all exceptions"""

    def __init__(self, message: Optional[str] = None):
        self.message = message


class _Meta(type):
    """Metaclass for defining exceptions."""

    def __call__(cls, *args: Any, **kwargs: Any) -> PyObsException:
        """Called when you call MyNewClass()"""
        exception: PyObsException = type.__call__(cls, *args, **kwargs)
        return handle_exception(exception)


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

    def __init__(self, module: Optional[str] = None, exception: Optional[PyObsException] = None):
        PyObsException.__init__(self, "A severe error has occurred.")
        self.module = module
        self.exception = exception


class LoggedException(NamedTuple):
    time: float
    exception: PyObsException


class ExceptionHandler(NamedTuple):
    exc_type: Type[PyObsException]
    limit: int
    callback: Callable[[PyObsException, Optional[str]], None]
    timespan: Optional[float] = None
    module: Optional[str] = None
    throw: bool = False


#######################################


_local_exceptions: Dict[Type[PyObsException], List[LoggedException]] = {}
_remote_exceptions: Dict[Tuple[Type[PyObsException], str], List[LoggedException]] = {}
_handlers: List[ExceptionHandler] = []


def clear() -> None:
    _local_exceptions.clear()
    _remote_exceptions.clear()
    _handlers.clear()


def register_exception(
    exc_type: Type[PyObsException],
    limit: int,
    callback: Callable[[PyObsException, Optional[str]], None],
    timespan: Optional[float] = None,
    module: Optional[str] = None,
    throw: bool = False,
) -> None:
    _handlers.append(ExceptionHandler(exc_type, limit, callback, timespan, module, throw))


def handle_exception(exception: PyObsException) -> PyObsException:
    # get module and store exception
    module = exception.module if isinstance(exception, RemoteException) else None

    # store exception itself
    _store_exception(exception, module)

    # if there is a child exception, store it as well
    if hasattr(exception, "exception"):
        _store_exception(getattr(exception, "exception"), module)

    # now check, whether something is severe
    triggered_handlers = _check_severity()

    # call all handlers
    for h in triggered_handlers:
        h.callback(exception, h.module)

    # if we got any handlers triggered and throw is set on any, escalate to a SevereException
    if len(triggered_handlers) > 0 and any([h.throw for h in triggered_handlers]):
        return SevereException(exception=exception, module=module)

    # else just return exception itself
    return exception


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
            if e not in _local_exceptions:
                _local_exceptions[e] = []
            _local_exceptions[e].append(le)

        else:
            # add to remote exceptions
            if (e, module) not in _remote_exceptions:
                _remote_exceptions[e, module] = []
            _remote_exceptions[e, module].append(le)


def _check_severity() -> List[ExceptionHandler]:
    """Checks all handlers against all raised exceptions and returns a list of triggered exception handlers.

    Returns:
        List of triggered handlers.
    """

    # loop all _handlers
    triggered: List[ExceptionHandler] = []
    for h in _handlers:
        # get all exceptions that this handler deals with
        exceptions = []
        if h.module is None:
            # add local exceptions
            if h.exc_type in _local_exceptions:
                exceptions.extend(_local_exceptions[h.exc_type])
        else:
            # add remote exceptions
            if (h.exc_type, h.module) in _remote_exceptions:
                exceptions.extend(_remote_exceptions[h.exc_type, h.module])

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
            # add to list
            triggered.append(h)

    # return full list
    return triggered


#######################################
