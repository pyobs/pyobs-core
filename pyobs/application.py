import logging
import signal
import threading
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
import yaml

from pyobs.object import get_object
from pyobs.modules import Module
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

    def run(self, config: str):
        """Actually run the application.

        Args:
            config: Name of config file, if any.
        """

        # everything in a try/except/finally, so that we can shut down gracefully
        try:
            # load config
            log.info('Loading configuration from {0:s}...'.format(config))
            with StringIO(pre_process_yaml(config)) as f:
                cfg = yaml.safe_load(f)

            # create module and open it
            log.info('Creating module...')
            self._module: Module = get_object(cfg)
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

            # finished
            log.info('Finished shutting down.')

    def _run(self):
        """Method that finally runs the module, can be overridden by derived classes."""

        # add signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # run module
        self._module.main()

    def _signal_handler(self, signum, frame):
        """React to signals and quit module."""
        self._module.quit()

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

