import logging
from contextlib import contextmanager
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import sessionmaker

from pytel.database.models.base import Base

log = logging.getLogger(__name__)


class Database:
    # global variables
    engine = None
    metadata = None
    session_maker = None

    @staticmethod
    def connect(connect: str = None, *args, **kwargs):
        """Create a new database connection.

        Args:
            connect: Connection string.
        """

        # create engine
        log.info('Connecting to database...')
        Database.engine = create_engine(connect, pool_size=100, pool_recycle=3600)
        Database.engine.echo = False
        event.listen(Database.engine, 'checkout', Database._checkout_listener)

        # and metadata
        Database.metadata = MetaData(Database.engine)

        # and session
        Database.session_maker = sessionmaker(bind=Database.engine)

        # and tables
        Database.create_tables()

        # success
        return True

    @staticmethod
    def create_tables():
        """Create tables in database."""
        Base.metadata.create_all(Database.engine, checkfirst=True)

    @staticmethod
    def _checkout_listener(dbapi_con, con_record, con_proxy):
        """Enable stay-alive ping

        see https://stackoverflow.com/questions/18054224/python-sqlalchemy-mysql-server-has-gone-away
        """
        try:
            try:
                if hasattr(dbapi_con, 'ping'):
                    dbapi_con.ping(False)
            except TypeError:
                dbapi_con.ping()
        except dbapi_con.OperationalError as exc:
            if exc.args[0] in (2006, 2013, 2014, 2045, 2055):
                raise DisconnectionError()
            else:
                raise


@contextmanager
def session_context():
    """Provide a transactional scope around a series of operations."""

    # get session
    session = Database.session_maker()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = ['Database', 'session_context']
