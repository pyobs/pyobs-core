import logging
import threading

from pytel.object import get_object
from pytel.database import Database

log = logging.getLogger(__name__)


class Application:
    """The Application class is the default type for top-level pytel objects."""

    _instance = None

    def __init__(self, vfs=None, comm=None, environment=None, database: str = None, module=None, plugins=None,
                 *args, **kwargs):
        """Create a new application.

        Args:
            vfs: A handler for the virtual file system.
            comm: The comm object to use.
            environment: The environment.
            database: Database connection string.
            module: The module to run within the application.
            plugins: Plugins to run along with the modules.
        """

        # store
        self._db_connect = database

        # closing event
        self.closing = threading.Event()

        # create vfs
        if vfs:
            self._vfs = get_object(vfs)
        else:
            from pytel.vfs import VirtualFileSystem
            self._vfs = VirtualFileSystem()

        # create environment
        self._environment = None
        if environment:
            self._environment = get_object(environment)

        # create comm module
        self._comm = None
        if comm:
            self._comm = get_object(comm)
        else:
            from pytel.comm.dummy import DummyComm
            self._comm = DummyComm()

        # create module to publish
        self._module = get_object(module, comm=self._comm, vfs=self._vfs, environment=self._environment)

        # link all together
        self._comm.module = self._module

        # plugins
        self._plugins = []
        if plugins:
            for cfg in plugins.values():
                plg = get_object(cfg)
                plg._comm = self._comm
                plg._environment = self._environment
                self._plugins.append(plg)

        # set "singleton"
        Application._instance = self

    @staticmethod
    def instance() -> 'Application':
        """Get single instance of application."""
        return Application._instance

    def open(self) -> bool:
        """Open application module and, if exist, comm, and plugin modules."""

        # connect database
        if self._db_connect:
            if not Database.connect(self._db_connect):
                log.error('Could not open database.')
                return False

        # open comm
        if self._comm:
            log.info('Opening comm...')
            if not self._comm.open():
                log.error('Could not open comm.')
                return False

        # open module
        log.info('Opening module...')
        self._module.open()

        # open plugins
        if self._plugins:
            log.info('Opening plugins...')
            for plg in self._plugins:
                plg.open()

        # success
        log.info('Started successfully.')
        return True

    def close(self):
        """Close application and all connected modules."""

        # close everything
        log.info('Closing plugins...')
        for plg in self._plugins:
            plg.close()
        log.info('Closing module...')
        self._module.close()

        # close comm
        if self._comm:
            log.info('Closing comm...')
            self._comm.close()

        # done closing
        log.info('Finished closing all modules.')

    def run(self):
        """Main loop for application."""
        while not self.closing.is_set():
            self.closing.wait(1)

    def quit(self):
        """Quit application."""
        self.closing.set()


def APP():
    return Application.instance()


__all__ = ['Application', 'APP']
