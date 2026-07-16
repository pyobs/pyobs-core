from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, NamedTuple

"""
TODO: Write docs
"""
__title__ = "Exceptions"


class PyobsError(Exception):
    """Base class for all exceptions"""

    _registry: dict[str, type[PyobsError]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        PyobsError._registry[f"{cls.__module__}.{cls.__qualname__}"] = cls

    def __init__(self, message: str | None = None, **context: Any) -> None:
        self.message = message
        self.logged = False
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        msg = f"<{self.__class__.__name__}>"
        if self.message is not None:
            msg += f" {self.message}"
        return msg

    def log(self, log: logging.Logger, level: str, message: str, **kwargs: Any) -> None:
        if self.logged:
            return
        log.log(logging.getLevelName(level), message, **kwargs)
        self.logged = True

    @classmethod
    def resolve(cls, qualified_name: str) -> type[PyobsError] | None:
        return cls._registry.get(qualified_name)


class _Meta(type):
    """Metaclass for defining exceptions."""

    def __call__(cls, *args: Any, **kwargs: Any) -> PyobsError:
        """Called when you call MyNewClass()"""
        exception: PyobsError = type.__call__(cls, *args, **kwargs)
        return handle_exception(exception)


#######################################


class ModuleError(PyobsError, metaclass=_Meta):
    pass


class GeneralError(PyobsError, metaclass=_Meta):
    pass


class ImageError(PyobsError, metaclass=_Meta):
    pass


class MotionError(PyobsError, metaclass=_Meta):
    pass


class InitError(MotionError, metaclass=_Meta):
    pass


class ParkError(MotionError, metaclass=_Meta):
    pass


class MoveError(MotionError, metaclass=_Meta):
    pass


class GrabImageError(PyobsError, metaclass=_Meta):
    pass


class AbortedError(PyobsError, metaclass=_Meta):
    pass


class FocusError(PyobsError, metaclass=_Meta):
    pass


class AcquisitionError(PyobsError, metaclass=_Meta):
    pass


class UnclassifiedError(PyobsError, metaclass=_Meta):
    """Wraps an exception that crossed an RPC boundary but couldn't be reconstructed as its real
    type -- either it was never a PyobsError to begin with (a builtin, a vendor SDK exception), or
    its defining module was never imported in this process. The original type name survives as
    `original_type` even when the class itself doesn't."""

    pass


#######################################


class RemoteError(PyobsError, metaclass=_Meta):
    """Exception for anything related to the communication between modules."""

    pass


class RemoteTimeoutError(RemoteError, metaclass=_Meta):
    pass


class ForbiddenError(RemoteError, metaclass=_Meta):
    """Raised when a caller is not permitted to invoke a method under the target module's ACL policy."""

    pass


#######################################


class SevereError(PyobsError):
    """Severe exception that is raised after multiple raised other exceptions."""

    def __init__(self, exception: PyobsError, module: str | None = None):
        PyobsError.__init__(self, "A severe error has occurred.")
        self.module = module
        # never encapsulate a SevereError
        self.exception: Exception = exception.exception if isinstance(exception, SevereError) else exception


class LoggedException(NamedTuple):
    time: float
    exception: PyobsError


class ExceptionHandler(NamedTuple):
    exc_type: type[PyobsError]
    limit: int
    timespan: float | None = None
    module: str | None = None
    callback: Callable[[PyobsError], Coroutine[Any, Any, None]] | None = None
    throw: bool = False


#######################################


_local_exceptions: dict[type[PyobsError], list[LoggedException]] = {}
_remote_exceptions: dict[tuple[type[PyobsError], str], list[LoggedException]] = {}
_handlers: list[ExceptionHandler] = []


def clear() -> None:
    _local_exceptions.clear()
    _remote_exceptions.clear()
    _handlers.clear()


def register_exception(
    exc_type: type[PyobsError],
    limit: int,
    timespan: float | None = None,
    module: str | None = None,
    callback: Callable[[PyobsError], Coroutine[Any, Any, None]] | None = None,
    throw: bool = False,
) -> None:
    _handlers.append(ExceptionHandler(exc_type, limit, timespan, module, callback, throw))


def handle_exception(exception: PyobsError) -> PyobsError:
    # get module and store exception -- "remote_module" is set by the RPC layer when reconstructing
    # a fault from another module (see rpc.py's _on_jabber_rpc_method_fault), not by local raises
    module = getattr(exception, "remote_module", None)

    # store exception itself
    _store_exception(exception, module)

    # if there is a child exception, store it as well
    if hasattr(exception, "exception"):
        _store_exception(getattr(exception, "exception"), module)

    # now check, whether something is severe
    triggered_handlers = _check_severity()

    # filter triggered handlers by those that actually handle the exception
    handlers = list(filter(lambda h: _matches(exception, h.exc_type), triggered_handlers))
    if hasattr(exception, "exception"):
        handlers += list(filter(lambda h: _matches(exception.exception, h.exc_type), triggered_handlers))

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


def _matches(exception: Exception, exc_type: type[PyobsError]) -> bool:
    """Whether `exception` should count as an instance of `exc_type` for severity-handler matching:
    true isinstance, or -- mirroring _store_exception's RemoteError special case below -- anything
    tagged with remote_module counts as a RemoteError even though its own type no longer literally
    subclasses it now that faults raise as their real type instead of wrapped."""
    if isinstance(exception, exc_type):
        return True
    return exc_type is RemoteError and getattr(exception, "remote_module", None) is not None


def _store_exception(exception: PyobsError, module: str | None) -> None:
    # get all classes from mro -- plus RemoteError if this crossed an RPC boundary (module is not
    # None, i.e. the exception carries a remote_module tag from rpc.py's fault reconstruction), even
    # though a directly-reraised domain type (e.g. GrabImageError) no longer subclasses RemoteError
    # itself now that faults raise as their real type instead of wrapped (see rpc.py, Assessment §A).
    # Preserves register_exception(exc.RemoteError, ..., module=X)-style "this module keeps failing
    # remotely, regardless of the specific type" handlers (e.g. AutoFocusSeries).
    classes: list[type] = list(type(exception).__mro__)
    if module is not None and RemoteError not in classes:
        classes.append(RemoteError)

    for e in classes:
        # only pyobs exceptions
        if not issubclass(e, PyobsError):
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


def _check_severity() -> list[ExceptionHandler]:
    """Checks all handlers against all raised exceptions and returns a list of triggered exception handlers.

    Returns:
        List of triggered handlers.
    """

    # loop all _handlers
    triggered: list[ExceptionHandler] = []
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
