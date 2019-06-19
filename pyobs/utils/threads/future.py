import threading

from pyobs.comm import TimeoutException
from pyobs.utils.types import cast_response_to_real


class Future(object):
    """
    Represents the result of an asynchronous computation.
    """

    def __init__(self):
        """
        Initializes a new Future.
        """
        self._value = None
        self._exception = None
        self._timeout = None
        self._signature = None
        self._event = threading.Event()

    def set_value(self, value):
        """
        Sets the value of this Future. Once the value is set, a caller
        blocked on get_value will be able to continue.
        """
        self._value = value
        self._event.set()

    def set_signature(self, sig):
        """Set the method signature."""
        self._signature = sig

    def wait(self):
        """
        Gets the value of this Future. This call will block until
        the result is available, or until the timeout expires.
        When this Future is cancelled with an error,
        """

        # wait a little first
        self._event.wait(10)

        # got an additional timeout?
        if self._timeout is not None and self._timeout > 10:
            self._event.wait(self._timeout - 10)

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

    def is_done(self):
        """
        Returns true if a value has been returned.
        """
        return self._event.is_set()

    def cancel_with_error(self, exception):
        """
        Cancels the Future because of an error. Once cancelled, a
        caller blocked on get_value will be able to continue.
        """
        self._exception = exception
        self._event.set()

    def set_timeout(self, timeout):
        """
        Sets a new timeout for the method call.
        """
        self._timeout = timeout

    def get_timeout(self):
        """
        Returns async timeout.
        """
        return self._timeout
