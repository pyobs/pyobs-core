import asyncio
import logging
import logging.handlers
import os
import platform
import signal
import warnings
from collections.abc import Awaitable, Callable
from io import StringIO
from typing import Any, TypedDict

import yaml

from pyobs.comm.dummy import DummyComm
from pyobs.modules import Module, MultiModule
from pyobs.object import get_class_from_string, get_object
from pyobs.utils.config import pre_process_yaml
from pyobs.utils.logging.context import ModuleNameFilter
from pyobs.utils.versions import loaded_pyobs_packages

# just init logger with something here, will be overwritten in __init__
log = logging.getLogger(__name__)


# --- IERS offline fallback ---------------------------------------------
# Skip live IERS/USNO downloads and rely on the astropy-iers-data snapshot bundled with the
# installed astropy package. Useful when the upstream IERS servers are down/unreachable/slow,
# or when running on a telescope control machine without reliable outbound internet access --
# astropy's own auto-refresh (IERS_Auto, triggered from inside coordinate transforms like
# Observer.altaz) does a synchronous network fetch inline wherever it's called from, which can
# stall an asyncio event loop for as long as that fetch takes if invoked from a module's main
# thread (see pyobs.modules.telescope.basetelescope._update_celestial_headers).
def _disable_iers_auto_download() -> None:
    from astropy.utils.iers import conf as iers_conf

    iers_conf.auto_download = False
    iers_conf.auto_max_age = None
    iers_conf.iers_degraded_accuracy = "warn"

    log.info(
        "IERS auto-download disabled — relying on the bundled astropy-iers-data snapshot. "
        "Earth orientation/UT1-UTC accuracy may degrade for predictions far from the "
        "snapshot date."
    )


# PYOBS_IERS_OFFLINE=1 kept as a standalone env-var trigger for anyone not going through the
# `pyobs` CLI's config/env machinery (e.g. importing Application directly). The CLI-driven path
# (Application.__init__'s iers_offline kwarg, wired from pyobs.cli.pyobs's GLOBAL_CONFIG_KEYS)
# calls the same _disable_iers_auto_download() below instead.
if os.environ.get("PYOBS_IERS_OFFLINE", "").lower() in ("1", "true", "yes"):
    _disable_iers_auto_download()
# -------------------------------------------------------------------------

# turn RuntimeWarnings into errors
warnings.filterwarnings("error", category=RuntimeWarning)


def _warm_iers_cache() -> None:
    """Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,
    synchronously.

    These are two independent auto-downloads: IERS_Auto.open() only covers UT1-UTC/polar
    motion. The leap-second table is fetched separately, on first use, by whatever Time
    conversion needs it -- update_leap_seconds() (not the lower-level LeapSeconds.auto_open())
    is the call that also installs the result into erfa so real usage later doesn't re-fetch.

    Meant to run inside an executor thread (see Application._main) -- calling this directly
    on the event loop would defeat the point.
    """
    from astropy.time.core import update_leap_seconds
    from astropy.utils.iers import IERS_Auto

    IERS_Auto.open()
    update_leap_seconds()


class InfluxLogConfig(TypedDict):
    url: str
    token: str
    org: str
    bucket: str


class Application:
    """Class for initializing and shutting down a pyobs process."""

    def __init__(
        self,
        config: str | None = None,
        module_factory: Callable[[], Awaitable[Module]] | None = None,
        loop_module_class: type[Module] | None = None,
        log_file: str | None = None,
        log_level: str = "info",
        syslog: bool = False,
        influx_log: InfluxLogConfig | None = None,
        iers_offline: bool = False,
        **kwargs: Any,
    ):
        """Initializes a pyobs application.

        Exactly one of `config`/`module_factory` must be given.

        Args:
            config: Name of config file.
            module_factory: Async factory that builds the Module once the event loop is already
                running, instead of parsing a config file synchronously in __init__ -- lets the
                factory `await` things (e.g. a login dialog's submit signal) before the module
                (and its comm connection) exists at all. Mutually exclusive with `config`.
            loop_module_class: Module class to pick `new_event_loop()` from when `module_factory`
                is given (the caller already knows which module class it's about to build, e.g.
                `GUI` in pyobs-gui's case). Required when `module_factory` is given, ignored
                otherwise.
            log_file: Name of log file, if any.
            log_level: Logging level.
            syslog: Send log to systemd journal, tagged with SYSLOG_IDENTIFIER=pyobs
                    and PYOBS_MODULE=<module name>. Requires logging-journald.
            iers_offline: Disable astropy's IERS/leap-second auto-download (see
                _disable_iers_auto_download's docstring above). Same effect as setting
                PYOBS_IERS_OFFLINE=1, but sourced from pyobs's own config/CLI machinery
                (pyobs.cli.pyobs's GLOBAL_CONFIG_KEYS) instead of a bare env var, so it applies
                the same way regardless of how the module process was spawned.
            influx_log: Log to influx DB.
        """
        if (config is None) == (module_factory is None):
            raise ValueError("Exactly one of 'config' or 'module_factory' must be given.")
        if module_factory is not None and loop_module_class is None:
            raise ValueError("loop_module_class is required when module_factory is given.")

        # get config name without path and extension
        self._config = config
        config_base = (
            os.path.splitext(os.path.basename(config))[0]
            if config is not None
            else loop_module_class.__name__.lower()  # type: ignore[union-attr]
        )

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

                # logging.CRITICAL and logging.FATAL are both 50, so the upstream LEVELS dict
                # literal collides and silently maps level 50 to FATAL's priority (0, "emerg")
                # instead of CRITICAL's (2, "crit"). Override explicitly to restore priority 2.
                LEVELS = {**JournaldLogHandler.LEVELS, logging.CRITICAL: 2}

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

        # set (maybe temporary) module name -- filename without leading underscores for the
        # config path, or a placeholder derived from loop_module_class for the factory path
        # (there's no real name yet until the factory resolves the actual module/comm identity)
        module_name.set(Path(self._config).stem.lstrip("_") if self._config is not None else config_base)

        # handlers/module-name context are set up above -- only now can a log.warning() here
        # actually reach journald tagged with PYOBS_MODULE, instead of falling through to
        # logging's untagged handler-of-last-resort
        if iers_offline:
            _disable_iers_auto_download()

        self._module: Module | None = None
        self._module_factory = module_factory

        if config is not None:
            # load config
            log.info("Loading configuration from %s...", config)
            with StringIO(pre_process_yaml(config)) as f:
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
            config_stem = Path(config).stem.lstrip("_")
            if "comm" not in cfg and not issubclass(klass, MultiModule):
                # no comm configured -- module would otherwise fall back to a DummyComm named
                # with the fixed placeholder "module", indistinguishable from every other
                # comm-less module in PYOBS_MODULE log tagging (see
                # specs/steering/finding-module-logs-under-pyobsd.md) and guaranteed to trip the
                # stem-mismatch check below. Give it the config file's own stem instead.
                cfg = {**cfg, "comm": {"class": f"{DummyComm.__module__}.{DummyComm.__name__}", "name": config_stem}}
            log.info("Creating module from class %s...", klass.__name__)
            try:
                self._module = get_object(cfg, Module)
            except Exception:
                # The module-creation failure (bad kwargs, broken __init__ chain, ...) is
                # otherwise only visible as an uncaught traceback on stderr -- which is
                # /dev/null for daemonized modules (--pid-file, as started by pyobsd /
                # pyobs-web-admin), so it silently vanishes from all logs. Record it through
                # the configured handlers (file/journald) before propagating.
                log.exception("Could not create module %s from config %s.", klass.__name__, config)
                raise

            # a config file whose stem doesn't match its own module's name silently splits
            # PYOBS_MODULE log tagging in two: logging that falls through both execute()
            # (module.py) and BackgroundTask (background_task.py) stays on the filename set
            # above, while logging covered by either of those uses the module's real
            # Comm-derived name -- refuse to start rather than let that drift run undetected.
            # MultiModule is exempt: its own .name is always the fixed placeholder "multi"
            # (module.py), never meant to match a filename -- each child module is already
            # correctly distinguished via execute()/BackgroundTask.
            if not isinstance(self._module, MultiModule):
                if self._module.name != config_stem:
                    log.warning(
                        "Config file stem (%s) does not match module's own name "
                        "(%s). Rename the config file or fix the module's "
                        "comm configuration so they match.",
                        config_stem,
                        self._module.name,
                    )
        else:
            # module_factory path: pick the event loop from the class the caller already knows
            # it's about to build -- the module itself gets built later, inside the running
            # loop (see _main()), since only there can the factory await anything.
            assert loop_module_class is not None  # validated above
            self._loop = loop_module_class.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def run(self) -> None:
        """Run app."""

        # run main task forever -- created before the signal handlers are registered below, so
        # a signal arriving the instant it's registered can never find self._main_task unset
        self._main_task = self._loop.create_task(self._main())

        # signals
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._loop.add_signal_handler(sig, self._signal_handler, sig)

        self._loop.run_forever()
        try:
            self._loop.run_until_complete(self._main_task)
        except asyncio.CancelledError:
            # _signal_handler() cancelled _main_task directly -- only reachable while
            # module_factory hadn't resolved yet (e.g. a login dialog still open), since
            # self._module.quit() is what normally unblocks run_forever()/main otherwise.
            pass
        except RuntimeError:
            # Qt-backed loops (qasync, used by pyobs-gui) can report the underlying Qt event
            # loop as stopped before _main_task is done -- e.g. when the GUI's native window
            # close triggers Qt's own quit independently of self._module.quit(). _main_task
            # keeps running as a plain asyncio task regardless; the cancel/gather below still
            # drains it, so this is a benign race in loop bookkeeping, not a failed shutdown.
            log.warning("Event loop reported as stopped before shutdown finished; continuing cleanup.")

        # main finished, cancel all tasks
        tasks = asyncio.all_tasks(self._loop)
        for t in tasks:
            log.debug("Task %s still running, cancelling it...", t)
            t.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        try:
            self._loop.run_until_complete(group)
        except RuntimeError:
            # same benign qasync race as above, now on the cancellation gather itself.
            log.warning("Event loop reported as stopped before task cancellation finished.")

        # finished
        log.info("Closing loop...")
        self._loop.close()

    def _signal_handler(self, sig: int) -> None:
        """React to signals and quit the module."""

        if self._module is not None:
            self._module.quit()
        else:
            # module_factory hasn't resolved yet (e.g. a login dialog still open) -- nothing to
            # quit, so cancel the pending factory wait directly instead. Module.quit() would
            # otherwise have called loop.stop() itself (module.py); mirror that here too.
            self._main_task.cancel()
            self._loop.stop()

        # reset signal handlers
        log.info("Got signal: %s, shutting down.", sig)
        loop = asyncio.get_running_loop()
        loop.remove_signal_handler(signal.SIGTERM)
        loop.add_signal_handler(signal.SIGINT, lambda: None)

    async def _main(self) -> None:
        """Actually run the application."""

        # everything in a try/except/finally, so that we can shut down gracefully
        try:
            # prime astropy's IERS earth-orientation cache now, before any module/comm/network
            # setup below -- left implicit, the first UT1-UTC lookup (e.g. basetelescope.py's
            # periodic celestial-header task, ~10-15s after startup) triggers astropy's
            # auto_download synchronously and blocks the event loop for however long that
            # download takes, at an unpredictable point during normal operation. Doing it here
            # in an executor keeps the download latency off the loop and confined to startup.
            # No-op (near-instant) when PYOBS_IERS_OFFLINE disabled auto_download above.
            try:
                await asyncio.get_running_loop().run_in_executor(None, _warm_iers_cache)
            except Exception:
                log.warning("Could not prime IERS earth-orientation data, continuing anyway.", exc_info=True)

            # resolve the module from the factory, if we're in that mode and haven't yet --
            # runs inside the running loop, so the factory can await anything it needs to
            # (e.g. a login dialog's submit signal) before the module/comm connection exists
            if self._module is None:
                assert self._module_factory is not None  # validated in __init__
                log.info("Waiting for module factory to resolve...")
                self._module = await self._module_factory()
                log.info("Module factory resolved.")

            # open module
            log.info("Opening module...")

            # record the loaded pyobs package versions for comm-less consumers (e.g. web-admin
            # reading the log/journal); both construction paths have finished importing everything
            # by this point. Guarded like the IERS priming above: metadata scanning can raise on
            # any installed distribution with broken dist-info, and that's not worth aborting
            # startup over.
            try:
                packages = loaded_pyobs_packages()
                log.info("Loaded pyobs packages: %s", ", ".join(f"{k}={v}" for k, v in packages.items()))
            except Exception:
                log.warning("Could not determine loaded pyobs package versions, continuing anyway.", exc_info=True)

            await self._module.startup()
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
