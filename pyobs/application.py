import logging
import os
import signal
import threading
import time
import warnings
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, Any, Dict

import yaml

from pyobs.object import get_object
from pyobs.modules import Module
from pyobs.utils.config import pre_process_yaml
from pyobs.utils.logger import DuplicateFilter

# just init logger with something here, will be overwritten in __init__
log = logging.getLogger(__name__)


class Application:
    """Class for initializing and shutting down a pyobs process."""

    def __init__(self, config: str, log_file: Optional[str] = None, log_level: str = 'info', log_rotate: bool = False,
                 **kwargs: Any):
        """Initializes a pyobs application.

        Args:
            config: Name of config file.
            log_file: Name of log file, if any.
            log_level: Logging level.
            log_rotate: Whether to rotate the log files.
        """

        # get config name without path and extension
        self._config = config

        # formatter for logging, and list of logging handlers
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')
        handlers = []

        # create stdout logging handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

        # create file logging handler, if log file is given
        if log_file is not None:
            file_handler: logging.FileHandler
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
        warnings.simplefilter('always', DeprecationWarning)

        # disable tornado logger
        logging.getLogger('tornado.access').disabled = True

        # set pyobs logger
        global log
        log = logging.getLogger(__name__)

        # hack threading to set thread names on OS level
        self._hack_threading()

        # init module with empty one
        self._module: Module = Module()

    def run(self) -> None:
        """Actually run the application.

        Args:
            config: Name of config file, if any.
        """

        # everything in a try/except/finally, so that we can shut down gracefully
        try:
            # load config
            log.info('Loading configuration from {0:s}...'.format(self._config))
            with StringIO(pre_process_yaml(self._config)) as f:
                cfg: Dict[str, Any] = yaml.safe_load(f)

            # create module and open it
            log.info('Creating module...')
            self._module = get_object(cfg, Module)
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

            # still threads running?
            if threading.active_count() > 1:
                # get logger
                wait_logger = logging.getLogger(__name__ + ':wait')
                wait_logger.addFilter(DuplicateFilter())

                # wait for them to end
                start_shutdown = time.time()
                while threading.active_count() > 1:
                    # print threads
                    names = [t.name for t in threading.enumerate() if t != threading.current_thread()]
                    wait_logger.info('Waiting for threads to close: ' + ','.join(names))

                    # after 30 seconds, kill everything
                    if time.time() - start_shutdown > 30:
                        wait_logger.error('Threads did not close gracefully, forcing exit...')
                        os._exit(0)

                    # wait a little
                    time.sleep(2)

            # finished
            log.info('Finished shutting down.')

    def _run(self) -> None:
        """Method that finally runs the module, can be overridden by derived classes."""

        # add signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # run module
        self._module.main()

    def _signal_handler(self, signum: Any, frame: Any) -> None:
        """React to signals and quit module."""
        self._module.quit()

    def _hack_threading(self) -> None:
        """Bad hack to set thread name on OS level."""
        try:
            import prctl

            def set_thread_name(name: str) -> None:
                prctl.set_name(name)

            def _thread_name_hack(self) -> None:
                set_thread_name(self.name)
                threading.Thread.__bootstrap_original__(self)

            threading.Thread.__bootstrap_original__ = threading.Thread._bootstrap
            threading.Thread._bootstrap = _thread_name_hack

        except ImportError:
            log = logging.getLogger('pyobs')
            log.warning('prctl module is not installed. You will not be able to see thread names')

            def set_thread_name(name: str) -> None:
                pass


class GuiApplication(Application):
    """Derived Application class that uses a Qt GUI. Allows for graceful shutdown in Windows."""

    def __init__(self, **kwargs: Any):
        """Create a new GUI application."""
        Application.__init__(self, **kwargs)

        # import Qt stuff
        from PyQt5.QtWidgets import QApplication
        from pyobs.utils.modulegui import ModuleGui
        import sys

        # create Qt app and window
        self._qapp = QApplication(sys.argv)
        self._window = ModuleGui()  # type: ignore

        # show window
        self._window.show()

    def _run(self) -> None:
        """Run qt application."""
        self._qapp.exec()


__all__ = ['Application', 'GuiApplication']
