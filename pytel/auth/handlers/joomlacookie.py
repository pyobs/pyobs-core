from contextlib import contextmanager
import tornado.web
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, mapper

from ..auth import AuthHandler


class JoomlaSession(object):
    pass


class JoomlaCookieAuthHandler(AuthHandler):
    """Allows access based on a set Joomla cookie."""

    def __init__(self, joomla_db: str = None, *args, **kwargs):
        """Created new Joomla cookie authentication handler.

        Args:
            joomla_db: Connect string for Joomla database.
        """

        # connect to database
        engine = create_engine(joomla_db, pool_size=100, pool_recycle=3600)
        metadata = MetaData(engine)
        table = Table('gw4ar_session', metadata, autoload=True)
        mapper(JoomlaSession, table)
        self._session = sessionmaker(bind=engine)

    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations."""
        session = self._session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

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

        # init db session
        with self.session() as session:
            # loop all cookies
            for tmp in request_handler.cookies.values():
                cookie = str(tmp)

                # we need a = in the cookie content
                if '=' in cookie:
                    # split by it, we need two elements
                    s = cookie.split('=')
                    if len(s) != 2:
                        continue
                    session_id = s[1]

                    # try to find it in database
                    data = session.query(JoomlaSession)\
                        .filter(JoomlaSession.session_id == session_id)\
                        .filter(JoomlaSession.userid != 0)\
                        .first()
                    if data is not None and data.userid > 0:
                        # we found a valid session for this user
                        return True

            # no valid session found
            return False


__all__ = ['JoomlaCookieAuthHandler']
