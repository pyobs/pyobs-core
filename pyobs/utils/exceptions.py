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
        exc(obj)
        return obj


#######################################


class RemoteException(PyObsException, metaclass=_Meta):
    """Remote exception encapsulating basic exception from other module"""

    def __init__(
        self, message: Optional[str] = None, module: Optional[str] = None, exception: Optional[PyObsException] = None
    ):
        PyObsException.__init__(self, message)
        self.module = module
        self.exception = exception


#######################################


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


class ExceptionLogger:
    def __init__(self) -> None:
        self.local_exceptions: Dict[Type[PyObsException], List[LoggedException]] = {}
        self.remote_exceptions: Dict[Tuple[Type[PyObsException], str], List[LoggedException]] = {}
        self.handlers: List[ExceptionHandler] = []

    def register(
        self,
        exc_type: Type[PyObsException],
        limit: int,
        timespan: Optional[float] = None,
        module: Optional[str] = None,
        callback: Optional[Callable[[Type[PyObsException], Optional[str]], None]] = None,
        throw: bool = True,
    ) -> None:
        self.handlers.append(ExceptionHandler(exc_type, limit, timespan, module, callback, throw))

    def __call__(self, exception: PyObsException) -> None:
        # get module and store exception
        module = exception.module if isinstance(exception, RemoteException) else None

        # store exception itself
        self._store(exception, module)

        # if there is a child exception, store it as well
        if hasattr(exception, "exception"):
            self._store(getattr(exception, "exception"), module)

        # now check, whether something is severe
        self._check_severe()

    def _store(self, exception: PyObsException, module: Optional[str]) -> None:
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
                if e not in self.local_exceptions:
                    self.local_exceptions[e] = []
                self.local_exceptions[e].append(le)

            else:
                # add to remote exceptions
                if (e, module) not in self.remote_exceptions:
                    self.remote_exceptions[e, module] = []
                self.remote_exceptions[e, module].append(le)

    def _check_severe(self) -> None:
        # loop all handlers
        for h in self.handlers:
            # get all exceptions that this handler deals with
            exceptions = []
            if h.module is None:
                # add local exceptions
                if h.exc_type in self.local_exceptions:
                    exceptions.extend(self.local_exceptions[h.exc_type])
            else:
                # add remote exceptions
                if (h.exc_type, h.module) in self.remote_exceptions:
                    exceptions.extend(self.remote_exceptions[h.exc_type, h.module])

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


exc = ExceptionLogger()


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


def cb(exc: Type[PyObsException], module: Optional[str] = None) -> None:
    print("callback", module, exc)


exc.register(MotionError, limit=3, callback=cb)

RemoteException(message="Hello world", module="telescope", exception=CannotInitError())
CannotParkError()
CannotInitError()

import pprint

pprint.pprint(exc.local_exceptions)
