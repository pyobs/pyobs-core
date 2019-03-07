class RemoteException(Exception):
    """
    Base exception for RPC. This exception is raised when a problem
    occurs in the network layer.
    """

    def __init__(self, message: str = "", cause=None):
        """
        Initializes a new RemoteException.

        Args:
            message: The message accompanying this exception.
            cause: The underlying cause of this exception.
        """
        self._message = message
        self._cause = cause
        pass

    def __str__(self):
        return self._message

    def get_message(self):
        return self._message

    def get_cause(self):
        return self._cause


class InvocationException(RemoteException):
    """
    Exception raised when a problem occurs during the remote invocation
    of a method.
    """
    pass


class AuthorizationException(RemoteException):
    """
    Exception raised when the caller is not authorized to invoke the
    remote method.
    """
    pass


class TimeoutException(RemoteException):
    """Exception raised on function call timeout."""
    pass


__all__ = ['RemoteException', 'InvocationException', 'AuthorizationException', 'TimeoutException']
