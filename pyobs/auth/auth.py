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


def tornado_auth_required(handler_class):
    """Decorator for tornado request handlers for dealing with authentication.

    Args:
        handler_class: Class to wrap.

    Returns:
        Wrapped class.
    """

    def wrap_execute(handler_execute):
        """Wrapper for the _execute method of the request handler.

        Args:
            handler_execute: The method to wrap.

        Returns:
            Wrapped method.
        """

        def handle_auth(handler, kwargs):
            """Handle authentification.

            Args:
                handler: Request handler to work on.

            Returns:
                Whether or not auth was successful.
            """

            # get auth handlers from tornado application
            auth_handlers = handler.application.auth_handlers
            if not auth_handlers:
                # if none are found, allow access
                return True

            # loop auth handlers
            success = False
            for auth_handler in auth_handlers:
                # check login with handler
                if auth_handler.check_login(request_handler=handler):
                    # successful login
                    success = True
                    break

            # no success?
            if not success:
                # get login handler
                login_handler = handler.application.login_handler
                if login_handler is not None:
                    # found login handler, call it
                    login_handler(handler)
                else:
                    # just throw an 401
                    handler.set_status(401)
                    handler._transforms = []
                    handler.write('Access denied')
                    handler.finish()
                    return False

            # finished
            return success

        def _execute(self, transforms, *args, **kwargs):
            """The new _execute method."""
            if not handle_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        # return the new _execute method.
        return _execute

    # wrap class and return it
    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


__all__ = ['AuthHandler', 'AuthDatabase', 'tornado_auth_required']
