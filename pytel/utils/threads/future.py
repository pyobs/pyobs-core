import threading

from pytel.comm import TimeoutException


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
        self._event = threading.Event()

    def set_value(self, value):
        """
        Sets the value of this Future. Once the value is set, a caller
        blocked on get_value will be able to continue.
        """
        self._value = value
        self._event.set()

    def get_value(self, timeout=None):
        """
        Gets the value of this Future. This call will block until
        the result is available, or until an optional timeout expires.
        When this Future is cancelled with an error,

        Arguments:
            timeout -- The maximum waiting time to obtain the value.
        """
        self._event.wait(timeout)
        if self._exception:
            raise self._exception
        if not self._event.is_set():
            raise TimeoutException
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
