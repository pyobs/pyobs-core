import logging
import os
import signal
import sys
import threading
import time
from io import StringIO
from logging.handlers import TimedRotatingFileHandler

import yaml

from pyobs.comm.dummy import DummyComm
from pyobs.object import get_object
from pyobs.modules import PyObsModule
from pyobs.comm import Comm
from pyobs.comm.xmpp import XmppComm
from pyobs.interfaces import IConfigProvider
from pyobs.utils.config import pre_process_yaml

log = None


class Application:
    """Class for initializing and shutting down a pyobs process."""

    def __init__(self, log_file: str = None, log_level: str = 'info', log_rotate: bool = False):
        """Initializes a pyobs application.

        Args:
            log_file: Name of log file, if any.
            log_level: Logging level.
            log_rotate: Whether to rotate the log files.
        """

        # formatter for logging, and list of logging handlers
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')
        handlers = []

        # create stdout logging handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

        # create file logging handler, if log file is given
        if log_file is not None:
            if log_rotate:
                # create automatically rotated log
                file_handler = TimedRotatingFileHandler(log_file, when='W0')
            else:
                # create simple file log
                file_handler = logging.FileHandler(log_file, mode='a')

            # add log file handler
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # basic setup
        logging.basicConfig(handlers=handlers, level=logging.getLevelName(log_level.upper()))
        logging.captureWarnings(True)

        # disable tornado logger
        logging.getLogger('tornado.access').disabled = True

        # set pyobs logger
        global log
        log = logging.getLogger(__name__)

        # hack threading to set thread names on OS level
        self._hack_threading()

        # for later
        self._comm = None
        self._module = None

    def run(self, config: str = None, username: str = None, password: str = None, server: str = None, comm: str = None):
        """Actually run the application.

        Args:
            config: Name of config file, if any.
            username: Username for server connection (overrides the one in config).
            password: Password for server connection (overrides the one in config).
            server: Server to connect to (overrides the one in config).
            comm: Type of comm object to use (overrides the one in config), defaults to 'xmpp'.
        """

        # everything in a try/except/finally, so that we can shut down gracefully
        try:
            # do we have a config?
            if config:
                # yes, load it
                log.info('Loading configuration from {0:s}...'.format(config))
                with StringIO(pre_process_yaml(config)) as f:
                    cfg = yaml.load(f)
            else:
                # create empty config
                cfg = {}

            # get comm object and open it
            log.info('Creating comm object...')
            self._comm = self._create_comm(cfg, username, password, server, comm)
            log.info('Opening connection to server...')
            self._comm.open()

            # remove comm from config, since we don't want to pass it to the module
            if 'comm' in cfg:
                del cfg['comm']

            # now, do we have a class definition?
            if 'class' not in cfg:
                log.info('No module definition found, trying to find a config provider and fetch get config...')

                # sleep a little to allow the comm object to get other clients
                time.sleep(2)

                # fetch network config
                cfg = self._get_network_config(self._comm)

                # still no config?
                if 'class' not in cfg:
                    raise ValueError('No configuration found.')
                else:
                    log.info('Successfully fetched module configuration from network.')

            # create module and open it
            log.info('Creating module...')
            self._module = get_object(cfg, comm=self._comm)   # type: PyObsModule
            log.info('Opening module...')
            self._module.open()
            log.info('Started successfully.')

            # run module
            self._run()

        except:
            # some exception was thrown
            log.exception('Something went wrong.')

        finally:
            # shutting down
            log.info('Shutting down...')

            # close module
            if self._module is not None:
                log.info('Closing module...')
                self._module.close()
            # close comm
            if self._comm is not None:
                log.info('Closing connection to server...')
                self._comm.close()

            # finished
            log.info('Finished shutting down.')

    def _run(self):
        """Method that finally runs the module, can be overridden by derived classes."""

        # add signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # run module
        self._module.run()

    def _signal_handler(self, signum, frame):
        """React to signals and quit module."""
        self._module.quit()

    def _create_comm(self, config: dict = None, username: str = None, password: str = None, server: str = None,
                     comm: str = None):
        """Create a comm object.

        If username/password are provided as parameters or in the environment, they are used. Otherwise those from
        the config are used.

        Args:
            config: Configuration dictionary.
            username: Username for server connection (overrides the one in config).
            password: Password for server connection (overrides the one in config).
            server: Server to connect to (overrides the one in config).
            comm: Type of comm object to use (overrides the one in config), defaults to 'xmpp'.

        Returns:
            A comm object.
        """

        # create comm object and return it
        if username is not None and password is not None and comm == 'xmpp':
            # create comm object from command line or environment
            return XmppComm(jid=username, password=password, server=server)
        else:
            if 'comm' in config:
                # create comm object from config
                return get_object(config['comm'])
            else:
                # create a dummy comm object
                return DummyComm()

    def _get_network_config(self, comm: Comm, attempts=10, wait_time=10) -> dict:
        """Fetches a configuration for the module from the network.

        Tries to find an IConfigProvider in the network and requests config from there.

        Args:
            comm: The comm object to use.
            attempts: Number of attempts before giving up.
            wait_time: Waiting time between attempts.

        Returns:
            The module configuration.
        """

        # loop IConfigProviders
        for client in comm.clients_with_interface(IConfigProvider):
            try:
                # get proxy
                proxy = comm[client]  # type: IConfigProvider

                # get config and return it
                return proxy.get_config(comm.name).wait()

            except FileNotFoundError:
                # seems that this config provider doesn't have a config for this client
                pass

        # seems we didn't find a config, try again?
        if attempts > 0:
            # sleep a little
            log.warning('No config found, trying to connect again in %d seconds...', wait_time)
            time.sleep(wait_time)

            # try again
            return self._get_network_config(comm, attempts=attempts - 1, wait_time=wait_time)

    def _hack_threading(self):
        """Bad hack to set thread name on OS level."""
        try:
            import prctl

            def set_thread_name(name):
                prctl.set_name(name)

            def _thread_name_hack(self):
                set_thread_name(self.name)
                threading.Thread.__bootstrap_original__(self)

            threading.Thread.__bootstrap_original__ = threading.Thread._bootstrap
            threading.Thread._bootstrap = _thread_name_hack

        except ImportError:
            log = logging.getLogger('pyobs')
            log.warning('prctl module is not installed. You will not be able to see thread names')

            def set_thread_name(name):
                pass


class GuiApplication(Application):
    """Derived Application class that uses a Qt GUI. Allows for graceful shutdown in Windows."""

    def __init__(self, *args, **kwargs):
        """Create a new GUI application."""
        Application.__init__(self, *args, **kwargs)

        # import Qt stuff
        from PyQt5.QtWidgets import QApplication
        from pyobs.utils.modulegui import ModuleGui
        import sys

        # create Qt app and window
        self._qapp = QApplication(sys.argv)
        self._window = ModuleGui()

        # show window
        self._window.show()

    def _run(self):
        """Run qt application."""
        self._qapp.exec()


__all__ = ['Application', 'GuiApplication']

