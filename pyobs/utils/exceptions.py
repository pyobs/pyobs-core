from __future__ import annotations

import asyncio
from collections import Coroutine
from typing import Optional, List, NamedTuple, Any, Tuple, Type, Dict, Callable
import time


class PyObsError(Exception):
    """Base class for all exceptions"""

    def __init__(self, message: Optional[str] = None):
        self.message = message

    def __str__(self) -> str:
        msg = f"<{self.__class__.__name__}>"
        if self.message is not None:
            msg += f" {self.message}"
        return msg


class _Meta(type):
    """Metaclass for defining exceptions."""

    def __call__(cls, *args: Any, **kwargs: Any) -> PyObsError:
        """Called when you call MyNewClass()"""
        exception: PyObsError = type.__call__(cls, *args, **kwargs)
        return handle_exception(exception)


#######################################


class ModuleError(PyObsError, metaclass=_Meta):
    pass


class MotionError(PyObsError, metaclass=_Meta):
    pass


class InitError(MotionError, metaclass=_Meta):
    pass


class ParkError(MotionError, metaclass=_Meta):
    pass


class MoveError(MotionError, metaclass=_Meta):
    pass


class GrabImageError(PyObsError, metaclass=_Meta):
    pass


#######################################


class RemoteError(PyObsError, metaclass=_Meta):
    """Exception for anything related to the communication between modules."""

    def __init__(self, module: str, message: Optional[str] = None):
        PyObsError.__init__(self, message)
        self.module = module


class RemoteTimeoutError(RemoteError, metaclass=_Meta):
    pass


class InvocationError(RemoteError, metaclass=_Meta):
    """Remote exception encapsulating basic exception from other module"""

    def __init__(self, module: str, exception: Exception):
        RemoteError.__init__(self, module, None)
        self.module = module
        a = ValueError()

        # never encapsulate a SevereError
        self.exception = exception.exception if isinstance(exception, SevereError) else exception

    def __str__(self) -> str:
        msg = f"<InvocationError> ({self.exception.__class__.__name__})"
        if hasattr(self.exception, "message"):
            if self.exception.message is not None:
                msg += f" {self.exception.message}"
        else:
            msg += f": {str(self.exception)}"
        return msg


#######################################


class SevereError(PyObsError):
    """Severe exception that is raised after multiple raised other exceptions."""

    def __init__(self, exception: PyObsError, module: Optional[str] = None):
        PyObsError.__init__(self, "A severe error has occurred.")
        self.module = module
        # never encapsulate a SevereError
        self.exception = exception.exception if isinstance(exception, SevereError) else exception


class LoggedException(NamedTuple):
    time: float
    exception: PyObsError


class ExceptionHandler(NamedTuple):
    exc_type: Type[PyObsError]
    limit: int
    timespan: Optional[float] = None
    module: Optional[str] = None
    callback: Optional[Callable[[PyObsError], Coroutine[Any, Any, None]]] = None
    throw: bool = False


#######################################


_local_exceptions: Dict[Type[PyObsError], List[LoggedException]] = {}
_remote_exceptions: Dict[Tuple[Type[PyObsError], str], List[LoggedException]] = {}
_handlers: List[ExceptionHandler] = []


def clear() -> None:
    _local_exceptions.clear()
    _remote_exceptions.clear()
    _handlers.clear()


def register_exception(
    exc_type: Type[PyObsError],
    limit: int,
    timespan: Optional[float] = None,
    module: Optional[str] = None,
    callback: Optional[Callable[[PyObsError], Coroutine[Any, Any, None]]] = None,
    throw: bool = False,
) -> None:
    _handlers.append(ExceptionHandler(exc_type, limit, timespan, module, callback, throw))


def handle_exception(exception: PyObsError) -> PyObsError:
    # get module and store exception
    module = exception.module if isinstance(exception, InvocationError) else None

    # store exception itself
    _store_exception(exception, module)

    # if there is a child exception, store it as well
    if hasattr(exception, "exception"):
        _store_exception(getattr(exception, "exception"), module)

    # now check, whether something is severe
    triggered_handlers = _check_severity()

    # filter triggered handlers by those that actually handle the exception
    handlers = list(filter(lambda h: isinstance(exception, h.exc_type), triggered_handlers))

    # check all handlers
    for h in handlers:
        # do we have a callback? then call it!
        if h.callback is not None:
            asyncio.create_task(h.callback(exception))

    # if we got any handlers triggered and throw is set on any, escalate to a SevereError
    if len(handlers) > 0 and any([h.throw for h in handlers]):
        return SevereError(exception=exception, module=module)

    # TODO: clean up old exceptions

    # else just return exception itself
    return exception


def _store_exception(exception: PyObsError, module: Optional[str]) -> None:
    # get all classes from mro
    for e in type(exception).__mro__:
        # only pyobs exceptions
        if not issubclass(e, PyObsError):
            continue

        # is it handled by any handler?
        if not any([e == h.exc_type for h in _handlers]):
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
