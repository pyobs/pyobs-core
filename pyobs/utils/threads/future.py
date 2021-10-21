import inspect
import threading
from typing import TypeVar, Generic, Optional, List, Any

from pyobs.comm.exceptions import TimeoutException
from pyobs.utils.types import cast_response_to_real


T = TypeVar('T')


class BaseFuture:
    def wait(self) -> Any:
        ...


class Future(BaseFuture, Generic[T]):
    """
    Represents the result of an asynchronous computation.
    """

    def __init__(self, value: Optional[T] = None, empty: bool = False, signature: Optional[inspect.Signature] = None):
        """
        Initializes a new Future.
        """
        self._value = value
        self._exception: Optional[Exception] = None
        self._timeout: Optional[float] = None
        self._signature: Optional[inspect.Signature] = signature
        self._event = threading.Event()

        # already set?
        if empty:
            # fire event
            self._event.set()

    def set_value(self, value: T) -> None:
        """
        Sets the value of this Future. Once the value is set, a caller
        blocked on get_value will be able to continue.
        """
        self._value = value
        self._event.set()

    def wait(self) -> Optional[T]:
        """
        Gets the value of this Future. This call will block until
        the result is available, or until the timeout expires.
        When this Future is cancelled with an error,
        """

        # no need to wait, if finished already
        if not self._event.is_set():
            # wait a little first
            self._event.wait(10)

            # got an additional timeout?
            if self._timeout is not None and self._timeout > 10:
                # we already waited 10s, so subtract it
                self._event.wait(self._timeout - 10.)

        # got an exception?
        if self._exception:
            raise self._exception

        # was timeout hit?
        if not self._event.is_set():
            raise TimeoutException

        # all ok, return value
        if self._signature is not None:
            # cast response to real types
            return cast_response_to_real(self._value, self._signature)
        else:
            return self._value

    def is_done(self) -> bool:
        """
        Returns true if a value has been returned.
        """
        return self._event.is_set()

    def cancel_with_error(self, exception: Exception) -> None:
        """
        Cancels the Future because of an error. Once cancelled, a
        caller blocked on get_value will be able to continue.
        """
        self._exception = exception
        self._event.set()

    def set_timeout(self, timeout: float) -> None:
        """
        Sets a new timeout for the method call.
        """
        self._timeout = timeout

    def get_timeout(self) -> Optional[float]:
        """
        Returns async timeout.
        """
        return self._timeout

    @staticmethod
    def wait_all(futures: List[BaseFuture]) -> List[Any]:
        return [fut.wait() for fut in futures if fut is not None]


__all__ = ['BaseFuture', 'Future']
