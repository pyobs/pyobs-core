import tornado.web


class AuthHandler:
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
        raise NotImplementedError


class AuthDatabase:
    def check_login(self, username: str, password: str) -> bool:
        """Checks the given credentials and decides whether access is granted or declined.

        Args:
            username (str): Username
            password (str): Password

        Returns:
            (bool) Whether to grant access.
        """
        raise NotImplementedError


__all__ = ['AuthHandler', 'AuthDatabase']
