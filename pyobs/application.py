import logging
import os
import signal
import threading
import time
from io import StringIO
from logging.handlers import TimedRotatingFileHandler

import yaml

from pyobs.object import get_object
from pyobs.modules import PyObsModule
from pyobs.comm import Comm
from pyobs.comm.xmpp import XmppComm
from pyobs.interfaces import IConfigProvider
from pyobs.utils.config import pre_process_yaml

log = None


class Application:
    def __init__(self, log_file: str = None, log_level: str = 'info', log_rotate: bool = False):

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

        # get pyobs logger
        global log
        log = logging.getLogger(__name__)

        # hack threading to set thread names on OS level
        self._hack_threading()

        # for later
        self._comm = None
        self._module = None

    def run(self, config: str = None, username: str = None, password: str = None, server: str = None, comm: str = None):
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
                log.info('No module definition found, trying to find a config provider...')
                cfg = self._get_network_config(self._comm, log, attempts=2)

            # still no config?
            if 'class' not in cfg:
                raise ValueError('No configuration found.')

            # create module and open it
            log.info('Creating module...')
            self._module = get_object(cfg, comm=self._comm)   # type: PyObsModule
            log.info('Opening module...')
            self._module.open()

            # add signal handlers
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

            # run module
            log.info('Started successfully.')
            self._module.run()

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

    def _signal_handler(self, signum, frame):
        self._module.quit()

    def _create_comm(self, config: dict = None, username: str = None, password: str = None, server: str = None,
                     comm: str = None):
        # get comm config from command line or environment, if given
        username = os.environ['USERNAME'] if username is None and 'USERNAME' in os.environ else username
        password = os.environ['PASSWORD'] if password is None and 'PASSWORD' in os.environ else password
        server = os.environ['SERVER'] if server is None and 'SERVER' in os.environ else server

        # create comm object and return it
        if username and password and comm == 'xmpp':
            # create comm object from command line or environment
            return XmppComm(jid=username, password=password, server=server)
        else:
            # create comm object from config
            return get_object(config['comm'])

    def _get_network_config(self, comm: Comm, log, attempts=10, wait_time=2) -> dict:
        # loop IConfigProviders
        for client in comm.clients_with_interface(IConfigProvider):
            try:
                # get proxy
                proxy = comm[client]  # type: IConfigProvider

                # get config and return it
                return proxy.get_config(comm.name)

            except FileNotFoundError:
                # seems that this config provider doesn't have a config for this client
                pass

        # seems we didn't find a config, try again?
        if attempts > 0:
            # sleep a little
            log.warning('No config found, trying to connect again in %d seconds...', wait_time)
            time.sleep(wait_time)

            # try again
            return self._get_network_config(comm, log, attempts=attempts - 1, wait_time=wait_time)

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
