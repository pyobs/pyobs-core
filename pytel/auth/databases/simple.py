from pytel.modules.module import PytelModule
from ..auth import AuthDatabase


class SimpleAuthDatabase(PytelModule, AuthDatabase):
    """Basic authentication module with fixed username/password."""

    def __init__(self, username: str = None, password: str = None, *args, **kwargs):
        """Creates new authentication database.

        Args:
            username: The expected username.
            password: The expected password.
        """
        PytelModule.__init__(self, *args, **kwargs)
        self._username = username
        self._password = password

    def check_login(self, username: str, password: str) -> bool:
        """Checks the given credentials and decides whether access is granted or declined.

        Args:
            username (str): Username
            password (str): Password

        Returns:
            (bool) Whether to grant access.
        """
        return username == self._username and password == self._password


__all__ = ['SimpleAuthDatabase']
