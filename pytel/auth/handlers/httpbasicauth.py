import base64
import tornado.web
from typing import Union, List

from ..auth import AuthHandler, AuthDatabase
from pytel.object import get_object


class HttpBasicAuthHandler(AuthHandler):
    """Allows access based on HTTP BASIC AUTH."""

    def __init__(self, database: Union[dict, AuthDatabase, List[AuthDatabase]] = None, *args, **kwargs):
        """Creates a new authentication handler based on HTTP AUTH.

        Args:
            database: Database(s) to check credentials against.
        """
        # create database(s)
        if not isinstance(database, list):
            database = [database]
        self._databases = [get_object(db, AuthDatabase) for db in database]

    def check_login(self, username: str = None, password: str = None,
                    request_handler: tornado.web.RequestHandler = None) -> bool:
        """Checks the given data for access.

        Args:
            username (str):          Username (if exists)
            password (str):          Password (if exists)
            request_handler(RequestHandler): HTTP request (if exists)

        Returns:
            (bool) Access granted or not.
        """

        # check header
        auth_header = request_handler.request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            return False

        # decode auth header and split
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 2)

        # check username and password
        for db in self._databases:
            if db.check_login(username, password):
                # successful login
                return True

        # no matching credentials found
        return False


class HttpBasicAuthLogin:
    def __init__(self, realm: str = 'pytel', *args, **kwargs):
        """Creates a new login handler.

        Args:
            realm: Realm to let Browser ask credentials for.
        """
        self._realm = realm

    def __call__(self, request_handler: tornado.web.RequestHandler = None, *args, **kwargs):
        """Force browser to show dialog for entering credentials.

        Args:
            request_handler: Tornado request handler that handles the current request.
        """
        request_handler.set_status(401)
        request_handler.set_header('WWW-Authenticate', 'Basic realm={0}'.format(self._realm))
        request_handler._transforms = []
        request_handler.finish()


__all__ = ['HttpBasicAuthHandler', 'HttpBasicAuthLogin']
