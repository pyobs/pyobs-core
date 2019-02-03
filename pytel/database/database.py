import logging
from contextlib import contextmanager
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import sessionmaker

from pytel.database.models.base import Base

log = logging.getLogger(__name__)


class Database:
    """Implements database methods for pytel."""

    def __init__(self, connect: str = None, table_prefix: str = 'pytel_', *args, **kwargs):
        """Create a new database connection.

        Args:
            connect: Connection string.
            table_prefix: Prefix for all pytel database tables.
        """

        # init
        self._engine = None
        self._metadata = None
        self._session = None
        self._connect = connect
        self._table_prefix = table_prefix

    def open(self):
        """Open database connection."""

        # create engine
        log.info('Connecting to database...')
        self._engine = create_engine(self._connect, pool_size=100, pool_recycle=3600)
        self._engine.echo = False
        event.listen(self._engine, 'checkout', Database._checkout_listener)

        # and metadata
        self._metadata = MetaData(self._engine)

        # and session
        self._session = sessionmaker(bind=self._engine)

        # success
        return True

    def create_tables(self):
        """Create tables in database."""

        # create tables
        Base.metadata.create_all(self._engine, checkfirst=True)

    def run(self):
        """This is just for running the Database object standalone for creating the database.
        All we do is creating the tables."""
        self.create_tables()

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


__all__ = ['Database']
