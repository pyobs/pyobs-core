import asyncio
import logging
import logging.handlers
import os
import platform
import signal
import warnings
import threading
from io import StringIO
from typing import Optional, Any, Dict, List, TypedDict
import yaml

from pyobs.object import get_object, get_class_from_string
from pyobs.modules import Module
from pyobs.utils.config import pre_process_yaml

# just init logger with something here, will be overwritten in __init__
log = logging.getLogger(__name__)


class InfluxLogConfig(TypedDict):
    url: str
    token: str
    org: str
    bucket: str


class Application:
    """Class for initializing and shutting down a pyobs process."""

    def __init__(
        self,
        config: str,
        log_file: Optional[str] = None,
        log_level: str = "info",
        influx_log: InfluxLogConfig | None = None,
        **kwargs: Any,
    ):
        """Initializes a pyobs application.

        Args:
            config: Name of config file.
            log_file: Name of log file, if any.
            log_level: Logging level.
            influx_log: Log to influx DB.
        """

        # get config name without path and extension
        self._config = config
        config_base = os.path.splitext(os.path.basename(config))[0]

        # formatter for logging, and list of logging handlers
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s")
        handlers: List[logging.Handler] = []

        # create stdout logging handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

        # create file logging handler, if log file is given
        if log_file is not None:
            # in Windows, append a FileHandler, otherwise we use a WatchedFileHandler, which works well with logrotate
            if platform.system() == "Windows":
                file_handler = logging.FileHandler(log_file)
            else:
                file_handler = logging.handlers.WatchedFileHandler(log_file)

            # add log file handler
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # influx handler?
        if influx_log is not None:
            from pyobs.utils.influxdb import InfluxHandler

            influx_logging_handler = InfluxHandler(**influx_log, module=config_base)
            handlers.append(influx_logging_handler)

        # basic setup
        logging.basicConfig(handlers=handlers, level=logging.getLevelName(log_level.upper()))
        logging.captureWarnings(True)
        warnings.simplefilter("always", DeprecationWarning)

        # disable tornado logger
        logging.getLogger("tornado.access").disabled = True

        # set pyobs logger
        global log
        log = logging.getLogger(__name__)

        # hack threading to set thread names on OS level
        self._hack_threading()

        # load config
        log.info("Loading configuration from {0:s}...".format(self._config))
        with StringIO(pre_process_yaml(self._config)) as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)

        # get module class
        class_name = cfg["class"]
        klass = get_class_from_string(class_name)

        # create event loop
        self._loop = klass.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # create module and open it
        log.info(f"Creating module from class {klass.__name__}...")
        self._module = get_object(cfg, Module)

    def run(self) -> None:
        """Run app."""

        # signals
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._loop.add_signal_handler(sig, self._signal_handler, sig)

        # run main task forever
        main = self._loop.create_task(self._main())
        self._loop.run_forever()
        self._loop.run_until_complete(main)

        # main finished, cancel all tasks
        tasks = asyncio.all_tasks(loop=self._loop)
        for t in tasks:
            log.debug(f"Task {t} still running, cancelling it...")
            t.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        self._loop.run_until_complete(group)

        # finished
        log.info("Closing loop...")
        self._loop.close()

    def _signal_handler(self, sig: int) -> None:
        """React to signals and quit module."""

        # stop loop
        # loop = asyncio.get_running_loop()
        # loop.stop()
        self._module.quit()

        # reset signal handlers
        log.info(f"Got signal: {sig!s}, shutting down.")
        loop = asyncio.get_running_loop()
        loop.remove_signal_handler(signal.SIGTERM)
        loop.add_signal_handler(signal.SIGINT, lambda: None)

    async def _main(self) -> None:
        """Actually run the application."""

        # everything in a try/except/finally, so that we can shut down gracefully
        try:
            # open module
            log.info("Opening module...")
            await self._module.open()
            log.info("Started successfully.")

            # run module
            await self._module.main()

        except:
            # some exception was thrown
            log.exception("Something went wrong.")

        finally:
            # shutting down
            log.info("Shutting down...")

            # close module
            if self._module is not None:
                log.info("Closing module...")
                try:
                    await self._module.close()
                except:
                    log.exception("hey")

            # finished
            log.info("Finished shutting down.")

    def _hack_threading(self) -> None:
        """Bad hack to set thread name on OS level."""
        try:
            import prctl

            def set_thread_name(name: str) -> None:
                prctl.set_name(name)

            def _thread_name_hack(this: Any) -> None:
                set_thread_name(this.name)
                threading.Thread.__bootstrap_original__(this)  # type: ignore

            threading.Thread.__bootstrap_original__ = threading.Thread._bootstrap  # type: ignore
            threading.Thread._bootstrap = _thread_name_hack  # type: ignore

        except ImportError:
            logger = logging.getLogger("pyobs")
            logger.warning("prctl module is not installed. You will not be able to see thread names")

            def set_thread_name(name: str) -> None:
                pass


class GuiApplication(Application):
    """Derived Application class that uses a Qt GUI. Allows for graceful shutdown in Windows."""

    def __init__(self, **kwargs: Any):
        """Create a new GUI application."""
        Application.__init__(self, **kwargs)

        # import Qt stuff
        from PySide6.QtWidgets import QApplication  # type: ignore
        from pyobs.utils.modulegui import ModuleGui
        import sys

        # create Qt app and window
        self._qapp = QApplication(sys.argv)
        self._window = ModuleGui()

        # show window
        self._window.show()

    def _run(self) -> None:
        """Run qt application."""
        self._qapp.exec()


__all__ = ["Application", "GuiApplication"]
