import asyncio
import logging
import logging.handlers
import os
import platform
import signal
import warnings
from io import StringIO
from typing import Any, TypedDict

import yaml

from pyobs.modules import Module
from pyobs.object import get_class_from_string, get_object
from pyobs.utils.config import pre_process_yaml
from pyobs.utils.logging.context import ModuleNameFilter

# just init logger with something here, will be overwritten in __init__
log = logging.getLogger(__name__)


# turn RuntimeWarnings into errors
warnings.filterwarnings("error", category=RuntimeWarning)


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
        log_file: str | None = None,
        log_level: str = "info",
        syslog: bool = False,
        influx_log: InfluxLogConfig | None = None,
        **kwargs: Any,
    ):
        """Initializes a pyobs application.

        Args:
            config: Name of config file.
            log_file: Name of log file, if any.
            log_level: Logging level.
            syslog: Send log to systemd journal, tagged with SYSLOG_IDENTIFIER=pyobs
                    and PYOBS_MODULE=<module name>. Requires logging-journald.
            influx_log: Log to influx DB.
        """

        # get config name without path and extension
        self._config = config
        config_base = os.path.splitext(os.path.basename(config))[0]

        # filter that injects %(pyobs_module)s into every LogRecord from the context var
        module_name_filter = ModuleNameFilter()

        # formatters — file/stream include the module name as text; journal omits
        # timestamp/priority since those are captured natively by journald
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(pyobs_module)s) %(filename)s:%(lineno)d %(message)s"
        )
        journal_formatter = logging.Formatter("%(pyobs_module)s %(filename)s:%(lineno)d %(message)s")

        handlers: list[logging.Handler] = []

        # create stdout logging handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(module_name_filter)
        handlers.append(stream_handler)

        # create file logging handler, if log file is given
        if log_file is not None:
            # in Windows, append a FileHandler, otherwise we use a WatchedFileHandler, which works well with logrotate
            if platform.system() == "Windows":
                file_handler = logging.FileHandler(log_file)
            else:
                file_handler = logging.handlers.WatchedFileHandler(log_file)

            file_handler.setFormatter(formatter)
            file_handler.addFilter(module_name_filter)
            handlers.append(file_handler)

        # systemd journal handler?
        if syslog:
            from logging_journald import JournaldLogHandler

            class PyobsJournaldLogHandler(JournaldLogHandler):
                """JournaldLogHandler that adds SYSLOG_IDENTIFIER=pyobs and PYOBS_MODULE per record."""

                def __init__(self, **kw: Any) -> None:
                    super().__init__(identifier="pyobs", **kw)

                def _format_record(self, record: logging.LogRecord) -> list[tuple[str, Any]]:
                    pairs: list[tuple[str, Any]] = super()._format_record(record)
                    pairs.append(("PYOBS_MODULE", getattr(record, "pyobs_module", "")))
                    return pairs

            journal_handler = PyobsJournaldLogHandler()
            journal_handler.setFormatter(journal_formatter)
            journal_handler.addFilter(module_name_filter)
            handlers.append(journal_handler)

        # influx handler?
        if influx_log is not None:
            from pyobs.utils.influxdb import InfluxHandler

            influx_logging_handler = InfluxHandler(**influx_log, module=config_base)
            handlers.append(influx_logging_handler)

        # basic setup
        logging.basicConfig(handlers=handlers, level=logging.getLevelName(log_level.upper()))
        logging.captureWarnings(True)
        warnings.simplefilter("always", DeprecationWarning)

        # change some loggers
        logging.getLogger("slixmpp.util.sasl.client").setLevel(logging.WARNING)

        # set pyobs logger
        global log
        from pathlib import Path

        from pyobs.utils.logging.context import module_name

        log = logging.getLogger(__name__)
        module_name.set(Path(self._config).stem)

        # load config
        log.info("Loading configuration from %s...", self._config)
        with StringIO(pre_process_yaml(self._config)) as f:
            cfg: dict[str, Any] = yaml.safe_load(f)

        # get module class
        class_name = cfg["class"]
        klass = get_class_from_string(class_name)

        # create event loop — if top-level class doesn't override new_event_loop,
        # check child modules for one that does (e.g. pyobs_gui.GUI in a MultiModule)
        loop_class = klass
        if klass.new_event_loop is Module.new_event_loop:
            for mod_cfg in cfg.get("modules", {}).values():
                if isinstance(mod_cfg, dict) and "class" in mod_cfg:
                    child_klass = get_class_from_string(mod_cfg["class"])
                    if child_klass.new_event_loop is not Module.new_event_loop:
                        loop_class = child_klass
                        break
        self._loop = loop_class.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # create module and open it
        log.info("Creating module from class %s...", klass.__name__)
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
        tasks = asyncio.all_tasks(self._loop)
        for t in tasks:
            log.debug("Task %s still running, cancelling it...", t)
            t.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        self._loop.run_until_complete(group)

        # finished
        log.info("Closing loop...")
        self._loop.close()

    def _signal_handler(self, sig: int) -> None:
        """React to signals and quit the module."""

        self._module.quit()

        # reset signal handlers
        log.info("Got signal: %s, shutting down.", sig)
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

        except Exception:
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
                except Exception:
                    log.exception("hey")

            # finished
            log.info("Finished shutting down.")


class GuiApplication(Application):
    """Derived Application class that uses a Qt GUI. Allows for graceful shutdown in Windows."""

    def __init__(self, **kwargs: Any):
        """Create a new GUI application."""
        Application.__init__(self, **kwargs)

        # import Qt stuff
        import sys

        from PySide6.QtWidgets import QApplication

        from pyobs.utils.modulegui import ModuleGui

        # create Qt app and window
        self._qapp = QApplication(sys.argv)
        self._window = ModuleGui()

        # show window
        self._window.show()

    def _run(self) -> None:
        """Run qt application."""
        self._qapp.exec()


__all__ = ["Application", "GuiApplication"]
