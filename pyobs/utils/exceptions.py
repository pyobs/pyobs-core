from __future__ import annotations

from typing import Optional, List, NamedTuple, Any, TypeVar, Type
import time

"""
Base class for all exceptions
"""


class PyObsException:
    def __init__(self, message: Optional[str] = None):
        self.message = message


T = TypeVar("T", bound=PyObsException)


class _Meta(type):
    """Metaclass for defining exceptions."""

    def __call__(cls, *args: Any, **kwargs: Any) -> PyObsException:
        """Called when you call MyNewClass()"""
        obj: PyObsException = type.__call__(cls, *args, **kwargs)
        exc(obj)
        return obj


"""
Remote exception encapsulating basic exception from other module
"""


class RemoteException(PyObsException, metaclass=_Meta):
    def __init__(
        self, message: Optional[str] = None, module: Optional[str] = None, exception: Optional[PyObsException] = None
    ):
        PyObsException.__init__(self, message)
        self.module = module
        self.exc = exception


"""
Counting raised exceptions
"""


class LoggedException(NamedTuple):
    time: float
    exception: PyObsException


class ExceptionLogger:
    def __init__(self) -> None:
        self.exceptions: List[LoggedException] = []

    def __call__(self, exception: PyObsException) -> None:
        self.exceptions.append(LoggedException(time=time.time(), exception=exception))
        print("added:", exception)
        print(exception.message)


exc = ExceptionLogger()


aa = RemoteException(message="Hello world")
