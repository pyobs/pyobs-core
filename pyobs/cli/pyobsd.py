from __future__ import annotations

import abc
import argparse
import glob
import json
import logging
import os
import pwd
import signal
import subprocess
import sys
import time
from typing import Any

import psutil

from pyobs.utils.shutdown import read_stop_deadline, stop_file_for

from ._cli import CLI, PYOBSD_MODE_ENV, PYOBSD_MODES, pyobsd_mode

log = logging.getLogger("pyobs")

# how long "stop --kill" waits for a killed module to be gone
_KILL_WAIT_SECONDS = 5.0


class PyobsDaemonCLI(CLI):
    """Class for initializing and running pyobsd CLI."""

    # name of section in configuration file
    CONFIG_SECTION = "pyobsd"

    # list of parameters that can be defined in the config file
    GLOBAL_CONFIG_KEYS = [
        "path",
        "config_path",
        "run_path",
        "log_path",
        "log_level",
        "syslog",
        "file_log",
        "chuid",
        "stop_timeout",
    ]
    # "mode" is not in GLOBAL_CONFIG_KEYS: pyobs reads it too, so it has its own lookup with $PYOBSD_MODE (see
    # pyobsd_mode), instead of the generic $PYOBS_<KEY>

    def init_cli(self) -> None:
        # mode, an invalid one is only an error for commands other than "setup", which can fix it
        self._mode_error: str | None = None
        try:
            mode = pyobsd_mode(self.file_config)
        except ValueError as e:
            self._mode_error = str(e)
            mode = "pid"
        self._parser.add_argument(
            "--mode",
            type=str,
            choices=PYOBSD_MODES,
            default=mode,
            help=f"run modules as daemons with PID files, or as systemd user units (default from ${PYOBSD_MODE_ENV} "
            "or pyobsd.mode in the config file, else pid)",
        )

        # init parser
        self._parser.add_argument("-p", "--path", type=str, default=self._config.get("path", "/opt/pyobs"))
        self._parser.add_argument("-c", "--config-path", type=str, default=self._config.get("config_path", "config"))
        self._parser.add_argument("-r", "--run-path", type=str, default=self._config.get("run_path", "run"))
        self._parser.add_argument("-l", "--log-path", type=str, default=self._config.get("log_path", "log"))
        self._parser.add_argument(
            "--log-level",
            type=str,
            choices=["critical", "error", "warning", "info", "debug"],
            default=self._config.get("log-level", "info"),
        )
        self._parser.add_argument(
            "--syslog",
            action=argparse.BooleanOptionalAction,
            help="send module logs to systemd journal (use --no-syslog to disable)",
            default=self._config.get("syslog", True),
        )
        self._parser.add_argument(
            "--file-log",
            action=argparse.BooleanOptionalAction,
            help="also write each module's log to <log-path>/<module>.log (off by default; use --file-log to enable)",
            default=self._config.get("file_log", False),
        )
        self._parser.add_argument("--chuid", type=str, default=self._config.get("chuid", "pyobs:pyobs"))
        self._parser.add_argument(
            "--stop-timeout",
            type=float,
            default=self._config.get("stop_timeout", 30.0),
            metavar="SECONDS",
            help="seconds to wait after SIGTERM before sending SIGKILL, unless the module asked for more time",
        )
        self._parser.add_argument("-v", "--verbose", action="store_true")

        # commands
        # metavar lists the commands for users, without the internal "exec"
        sp = self._parser.add_subparsers(dest="command", metavar="{start,stop,restart,status,list,logs,setup}")
        sp.add_parser("start", help="start modules").add_argument("modules", type=str, nargs="*")
        stop_parser = sp.add_parser("stop", help="stop modules")
        stop_parser.add_argument("modules", type=str, nargs="*")
        stop_parser.add_argument(
            "--no-wait", action="store_true", help="only send SIGTERM, do not wait for the modules to exit"
        )
        stop_parser.add_argument(
            "--kill",
            action="store_true",
            help="send SIGKILL right away, e.g. for a module whose shutdown hangs (cuts a camera's warm-up)",
        )
        restart_parser = sp.add_parser("restart", help="restart modules")
        restart_parser.add_argument("modules", type=str, nargs="*")
        restart_parser.add_argument(
            "--kill", action="store_true", help="send SIGKILL right away instead of a normal stop, then start"
        )
        status_parser = sp.add_parser("status", help="status of modules")
        status_parser.add_argument("--json", action="store_true")
        status_parser.add_argument(
            "--cpu-interval",
            type=float,
            default=None,
            metavar="SECONDS",
            help="measure CPU%% over this many seconds (shared across all modules, one sleep "
            "total, not one per module); omitted by default since it makes status blocking",
        )
        sp.add_parser("list", help="list of modules")
        sp.add_parser("logs", help="show/follow module logs via journalctl").add_argument(
            "args", nargs=argparse.REMAINDER, help="[module] [journalctl arguments...]"
        )
        self._add_setup_parser(sp)
        # internal: what the systemd unit runs, replaces pyobsd with "pyobs" for the module, in the foreground
        sp.add_parser("exec").add_argument("module", type=str)

    @staticmethod
    def _add_setup_parser(sp: Any) -> None:
        # own dests (setup_*), so they don't clash with the global options of the same name; None means "not given"
        p = sp.add_parser(
            "setup",
            help="set up this host for pyobsd (as root): user, directories, /etc/pyobs.yaml",
            description="Set up this host for pyobsd. Asks for every value not given as an option, unless -y is "
            "given or stdin is not a terminal. Run as root.",
        )
        p.add_argument("--mode", dest="setup_mode", choices=PYOBSD_MODES, default=None)
        p.add_argument("--user", dest="setup_user", metavar="USER[:GROUP]", default=None, help="the user for pyobs")
        p.add_argument(
            "--create-user",
            dest="setup_create_user",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="create the user if it doesn't exist (never done unattended without this)",
        )
        p.add_argument("--path", dest="setup_path", metavar="DIR", default=None, help="base path")
        p.add_argument(
            "--syslog",
            dest="setup_syslog",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="log to the systemd journal",
        )
        p.add_argument(
            "--file-log",
            dest="setup_file_log",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="also write log files",
        )
        p.add_argument("-y", "--yes", dest="setup_yes", action="store_true", help="ask nothing, don't confirm")
        p.add_argument("--strict", dest="setup_strict", action="store_true", help="exit with 1 on warnings")

    def run(self) -> None:
        if self._config["command"] == "setup":
            self._run_setup()
            return
        if self._mode_error is not None:
            self._parser.error(self._mode_error)

        # "exec" is the same in both modes
        if self._config["mode"] == "systemd" and self._config["command"] != "exec":
            print("The systemd mode is not implemented in this version of pyobsd yet.")
            sys.exit(1)

        # init daemon
        daemon: PyobsDaemonBase = PidFileDaemon(
            str(os.path.join(self._config["path"], self._config["config_path"])),
            str(os.path.join(self._config["path"], self._config["run_path"])),
            str(os.path.join(self._config["path"], self._config["log_path"])),
            log_level=self._config["log_level"],
            syslog=self._config["syslog"],
            file_log=self._config["file_log"],
            chuid=self._config["chuid"],
            stop_timeout=self._config["stop_timeout"],
            verbose=self._config["verbose"],
        )

        # run
        match self._config["command"]:
            case "start":
                daemon.start(modules=self._config["modules"])
            case "stop":
                if self._config["kill"]:
                    daemon.kill(modules=self._config["modules"])
                else:
                    daemon.stop(modules=self._config["modules"], wait=not self._config["no_wait"])
            case "restart":
                daemon.restart(modules=self._config["modules"], kill=self._config["kill"])
            case "status":
                daemon.status(print_json=self._config["json"], cpu_interval=self._config["cpu_interval"])
            case "list":
                daemon.list_modules()
            case "logs":
                daemon.logs(self._config["args"])
            case "exec":
                daemon.exec_module(self._config["module"])

    def _run_setup(self) -> None:
        from ._setup import Setup, SetupOptions

        c = self._config
        options = SetupOptions(
            mode=c["setup_mode"],
            user=c["setup_user"],
            create_user=c["setup_create_user"],
            path=c["setup_path"],
            syslog=c["setup_syslog"],
            file_log=c["setup_file_log"],
            yes=c["setup_yes"],
            strict=c["setup_strict"],
        )
        sys.exit(Setup(options, self.file_config)())


class PyobsDaemonBase(abc.ABC):
    """What both modes of pyobsd share: module names, config files, process info, logs."""

    def __init__(
        self,
        config_path: str,
        run_path: str,
        log_path: str,
        log_level: str = "info",
        syslog: bool = False,
        file_log: bool = False,
        chuid: str | None = None,
        stop_timeout: float = 30.0,
        verbose: bool = False,
        **kwargs: Any,
    ):
        self._config_path = config_path
        self._stop_timeout = stop_timeout
        self._run_path = run_path
        self._log_path = log_path
        self._log_level = log_level
        self._syslog = syslog
        self._file_log = file_log
        self._verbose = verbose

        # parse optional user/group from chuid (format: "user:group" or "user")
        self._user: str | None = None
        self._group: str | None = None
        if chuid:
            parts = chuid.split(":", 1)
            self._user = parts[0] or None
            self._group = parts[1] if len(parts) > 1 else None

        # find pyobs executable
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "pyobs"),
            "/usr/bin/pyobs",
            "/usr/local/bin/pyobs",
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                self._pyobs_exec = candidate
                break
        else:
            self._error("Could not find pyobs executable.")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _error(self, message: str) -> None:
        print(message)
        sys.exit(1)

    @staticmethod
    def _module(path: str) -> str:
        """Return the bare module name from a config or PID file path."""
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def _strip_disabled(module: str) -> str:
        """Strip a leading underscore, which marks a module as disabled.

        PID and log files are named after the "active" form of a module, so that
        toggling a module between enabled/disabled (by adding/removing the leading
        underscore on its config file) does not change its PID/log file names.
        """
        return module[1:] if module.startswith("_") else module

    def _config_file(self, module: str) -> str:
        return os.path.join(self._config_path, module + ".yaml")

    def _log_file(self, module: str) -> str:
        return os.path.join(self._log_path, self._strip_disabled(module) + ".log")

    def _list_configs(self) -> list[str]:
        """Return sorted module names from *.yaml files, excluding *.shared.yaml."""
        paths = sorted(glob.glob(os.path.join(self._config_path, "*.yaml")))
        return [self._module(p) for p in paths if not p.endswith(".shared.yaml")]

    def _process_info(self, pid: int) -> dict[str, Any]:
        """Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a
        shared sampling window across all processes, see _sample_cpu_percent."""
        try:
            proc = psutil.Process(pid)
            uptime = time.time() - proc.create_time()
            rss_mb = proc.memory_info().rss / 1024 / 1024
            return {"uptime": uptime, "rss_mb": rss_mb}
        except psutil.NoSuchProcess:
            return {"uptime": 0.0, "rss_mb": 0.0}

    @staticmethod
    def _sample_cpu_percent(pids: list[int], interval: float) -> dict[int, float]:
        """Sample CPU% for multiple PIDs over one shared interval, instead of the
        interval-per-process cost of calling Process.cpu_percent(interval=...) serially --
        that would take len(pids) * interval seconds and grows with the number of modules.
        psutil.cpu_percent(interval=None) after construction always returns 0.0 (it has no
        prior sample to diff against); it's the second, unblocked call after the shared
        sleep that reports the percentage actually elapsed, so pids share a single sleep.
        """
        procs = {}
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                proc.cpu_percent(interval=None)  # prime -- discard the meaningless 0.0
                procs[pid] = proc
            except psutil.NoSuchProcess:
                continue
        time.sleep(interval)
        result = {}
        for pid, proc in procs.items():
            try:
                result[pid] = proc.cpu_percent(interval=None)
            except psutil.NoSuchProcess:
                result[pid] = 0.0
        return result

    @staticmethod
    def _fmt_uptime(seconds: float) -> str:
        seconds = int(seconds)
        d, rem = divmod(seconds, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        if d:
            return f"{d}d {h:02d}:{m:02d}:{s:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def _fmt_wait(seconds: float) -> str:
        seconds = max(0, int(seconds))
        if seconds < 120:
            return f"{seconds} s"
        return f"{round(seconds / 60)} min"

    # ── public commands ───────────────────────────────────────────────────────

    @abc.abstractmethod
    def start(self, modules: list[str] | None = None) -> None:
        """Starts the given modules, or all enabled ones."""

    @abc.abstractmethod
    def stop(self, modules: list[str] | None = None, wait: bool = True) -> None:
        """Stops the given modules, or all running ones. With wait=False, does not wait for them to exit."""

    @abc.abstractmethod
    def kill(self, modules: list[str] | None = None) -> None:
        """Kills the given modules, or all running ones, without a shutdown."""

    @abc.abstractmethod
    def restart(self, modules: list[str] | None = None, kill: bool = False) -> None:
        """Restarts the given modules. With kill=True, kills them instead of a normal stop."""

    @abc.abstractmethod
    def status(self, print_json: bool = False, cpu_interval: float | None = None) -> None:
        """Prints the status of all modules."""

    def _pyobs_args(self, module: str) -> list[str]:
        """Options and config file for running a module with pyobs, the same in both modes."""
        args = [
            "--log-level",
            self._log_level,
            # the module ends itself if its shutdown takes longer than this (or what it asked for)
            "--stop-timeout",
            str(self._stop_timeout),
            self._config_file(module),
        ]
        if self._file_log:
            os.makedirs(self._log_path, exist_ok=True)
            args += ["--log-file", self._log_file(module)]
        if self._syslog:
            args.append("--syslog")
        return args

    def _find_config(self, name: str) -> str | None:
        """The config of a module by its active name: "<name>", or else the disabled "_<name>". A leading
        underscore in name is ignored. None if neither exists."""
        active = self._strip_disabled(name)
        configs = self._list_configs()
        for module in (active, "_" + active):
            if module in configs:
                return module
        return None

    def exec_module(self, name: str) -> None:
        """Replaces this process with pyobs running the module in the foreground, without a PID file.

        This is what the systemd unit runs ("pyobsd exec %i", with the active name). The process keeps its PID,
        so pyobs is the unit's main process and can notify systemd. Runs as the calling user, chuid is not used.
        """
        module = self._find_config(name)
        if module is None:
            self._error(f"Module {name!r} does not exist.")
            return
        cmd = [self._pyobs_exec, *self._pyobs_args(module)]
        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")
        sys.stdout.flush()
        os.execv(self._pyobs_exec, cmd)

    def list_modules(self) -> None:
        print("\n".join(self._list_configs()))

    def logs(self, args: list[str]) -> None:
        """Show/follow module logs by exec'ing into journalctl."""
        match_args = ["SYSLOG_IDENTIFIER=pyobs"]
        remainder = list(args)
        # "--" may have been auto-inserted by main() to work around argparse.REMAINDER
        # refusing to swallow a leading flag (e.g. "pyobsd logs -f") — drop it here.
        if remainder and remainder[0] == "--":
            remainder.pop(0)
        if remainder and remainder[0] in self._list_configs():
            match_args.append(f"PYOBS_MODULE={remainder.pop(0)}")
        cmd = ["journalctl", *match_args, *remainder]
        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")
        os.execvp("journalctl", cmd)


class PidFileDaemon(PyobsDaemonBase):
    """PID-file mode: runs modules as daemons (pyobs --pid-file) and tracks them by their PID files."""

    # ── helpers ───────────────────────────────────────────────────────────────

    def _pid_file(self, module: str) -> str:
        return os.path.join(self._run_path, self._strip_disabled(module) + ".pid")

    def _stop_file(self, module: str) -> str:
        """Where a stopping module writes its shutdown deadline (see pyobs.utils.shutdown)."""
        return stop_file_for(self._pid_file(module))

    def _read_pid(self, module: str) -> int | None:
        """Read and return the PID from the module's PID file, or None."""
        pid_file = self._pid_file(module)
        if not os.path.exists(pid_file):
            return None
        try:
            with open(pid_file) as f:
                return int(f.read().strip())
        except (ValueError, OSError):
            return None

    def _is_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _running_pid(self, module: str) -> int | None:
        """Return the live PID for a module, or None. Cleans up stale PID files."""
        pid = self._read_pid(module)
        if pid is None:
            return None
        if self._is_alive(pid):
            return pid
        # stale PID file — remove it, together with a stop file the process may have left behind
        self._remove_run_files(module)
        return None

    def _stop_deadline(self, module: str) -> float | None:
        """The deadline a running module wrote into its stop file, or None if it is not stopping."""
        return read_stop_deadline(self._stop_file(module))

    # ── public commands ───────────────────────────────────────────────────────

    def start(self, modules: list[str] | None = None) -> None:
        configs = self._list_configs()

        # if no modules given, start all non-underscore configs
        if not modules:
            modules = [m for m in configs if not m.startswith("_")]

        for module in sorted(modules):
            if module not in configs:
                print(f"Module {module!r} does not exist.")
                sys.exit(1)
            if self._running_pid(module) is not None:
                print(f"{module} already running.")
            else:
                print(f"Starting {module}...")
                self._start_service(module)

    def stop(self, modules: list[str] | None = None, wait: bool = True) -> None:
        # if no modules given, stop all that have a live PID
        if not modules:
            modules = [m for m in self._list_configs() if self._running_pid(m) is not None]

        # send SIGTERM to all first, then wait for all together, so that one module with a long shutdown
        # (e.g. a camera warming up) does not delay sending SIGTERM to the others
        stopping: dict[str, int] = {}
        for module in modules:
            print(f"Stopping {module}...")
            pid = self._signal_stop(module)
            if pid is not None:
                stopping[module] = pid

        if wait:
            try:
                self._wait_stopped(stopping)
            except KeyboardInterrupt:
                # the modules run in their own session and keep shutting down without us
                print("\nStopped waiting.")
                now = time.time()
                for module, pid in stopping.items():
                    if not self._is_alive(pid):
                        continue
                    deadline = read_stop_deadline(self._stop_file(module))
                    until = ""
                    if deadline is not None and deadline > now:
                        until = f" (up to {self._fmt_wait(deadline - now)})"
                    print(f'{module} keeps shutting down in the background{until}, see "pyobsd status".')
                sys.exit(130)

    def kill(self, modules: list[str] | None = None) -> None:
        """Sends SIGKILL right away, without a shutdown, e.g. to a module whose shutdown hangs, and removes its run
        files. Without modules, kills all that have a live PID."""
        if not modules:
            modules = [m for m in self._list_configs() if self._running_pid(m) is not None]

        killed: dict[str, int] = {}
        for module in modules:
            pid = self._running_pid(module)
            if pid is None:
                print(f"{module} is not running.")
                continue
            print(f"Killing {module}...")
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
            killed[module] = pid

        # SIGKILL can't end a process stuck in the kernel (e.g. in a USB driver call) until that call returns. Keep
        # the PID file of such a process, so that it doesn't show as stopped and can't be started a second time
        deadline = time.time() + _KILL_WAIT_SECONDS
        while killed:
            for module, pid in list(killed.items()):
                if not self._is_alive(pid):
                    self._remove_run_files(module)
                    del killed[module]
            if not killed or time.time() >= deadline:
                break
            time.sleep(0.1)
        for module, pid in killed.items():
            print(f"{module} (PID {pid}) is still alive after SIGKILL, probably stuck in a driver call.")
        if killed:
            sys.exit(1)

    def restart(self, modules: list[str] | None = None, kill: bool = False) -> None:
        if kill:
            self.kill(modules=modules)
        else:
            self.stop(modules=modules)
        time.sleep(1)
        self.start(modules=modules)

    def status(self, print_json: bool = False, cpu_interval: float | None = None) -> None:
        configs = self._list_configs()
        # map "active" (no leading underscore) name -> config name, so that
        # PID files (always named without underscore) can be matched back to
        # their (possibly disabled) config
        active_to_config = {self._strip_disabled(m): m for m in configs}

        # also include any orphaned PID files not backed by a config
        pid_stems = [self._module(p) for p in glob.glob(os.path.join(self._run_path, "*.pid"))]
        modules = sorted(set(configs) | {active_to_config.get(s, s) for s in pid_stems})

        pids = {module: pid for module in modules if (pid := self._running_pid(module)) is not None}
        # CPU% is off by default -- a meaningful reading needs a real sampling window (see
        # _sample_cpu_percent), and forcing that cost on every plain "status" call would make
        # it slow for no benefit when nobody's looking at CPU. Only pay for it if asked.
        cpu_by_pid = self._sample_cpu_percent(list(pids.values()), cpu_interval) if cpu_interval else {}

        # a running module with a stop file is shutting down (see pyobs.utils.shutdown)
        deadlines = {module: self._stop_deadline(module) for module in pids}
        now = time.time()

        if print_json:
            # "running" stays true while a module is stopping (its process is still alive), so consumers that only
            # know "running" keep working; "state" tells them apart
            result: dict[str, Any] = {}
            for module in modules:
                pid = pids.get(module)
                if pid is not None:
                    info = self._process_info(pid)
                    deadline = deadlines[module]
                    result[module] = {
                        "running": True,
                        "state": "stopping" if deadline is not None else "running",
                        "stop_deadline": deadline,
                        "pid": pid,
                        "cpu": cpu_by_pid.get(pid),
                        **info,
                    }
                else:
                    result[module] = {"running": False, "state": "stopped"}
            print(json.dumps(result))
        else:
            # header
            print(f"{'module':<30}  {'status':<8}  {'uptime':>12}  {'cpu':>6}  {'rss':>8}")
            print("-" * 72)
            for module in modules:
                pid = pids.get(module)
                if pid is not None:
                    info = self._process_info(pid)
                    cpu = cpu_by_pid.get(pid)
                    cpu_str = f"{cpu:>5.1f}%" if cpu is not None else f"{'-':>6}"
                    deadline = deadlines[module]
                    state = "stopping" if deadline is not None else "running"
                    wait = (
                        f"  (up to {self._fmt_wait(deadline - now)})" if deadline is not None and deadline > now else ""
                    )
                    print(
                        f"{module:<30}  {state:<8}  "
                        f"{self._fmt_uptime(info['uptime']):>12}  "
                        f"{cpu_str}  "
                        f"{info['rss_mb']:>6.1f} MB"
                        f"{wait}"
                    )
                else:
                    print(f"{module:<30}  {'stopped':<8}")

    # ── process management ────────────────────────────────────────────────────

    def _start_service(self, module: str) -> None:
        os.makedirs(self._run_path, exist_ok=True)

        # a stop file left behind by a previous run (e.g. killed during warm-up) must not apply to this one
        try:
            os.remove(self._stop_file(module))
        except FileNotFoundError:
            pass

        cmd = [self._pyobs_exec, "--pid-file", self._pid_file(module), *self._pyobs_args(module)]

        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")

        # pyobs refuses --pid-file if the config says systemd mode, but this pyobsd runs in PID-file mode (e.g. with
        # --mode pid), so pass that on
        env = os.environ.copy()
        env[PYOBSD_MODE_ENV] = "pid"
        kwargs: dict[str, Any] = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # detach from pyobsd's process group
            env=env,
        )
        if self._user:
            kwargs["user"] = self._user
            # subprocess.Popen(user=...) switches uid but does NOT touch the
            # environment, so HOME would stay /root — breaking anything that
            # writes to $HOME (astropy cache, matplotlib config, etc.).
            # Mimic `su`/`sudo -u` and set HOME/USER/LOGNAME for the target user.
            try:
                pw = pwd.getpwnam(self._user)
                env["HOME"] = pw.pw_dir
                env["USER"] = self._user
                env["LOGNAME"] = self._user
            except KeyError:
                self._error(f"User {self._user!r} not found.")
        if self._group:
            kwargs["group"] = self._group

        proc = subprocess.Popen(cmd, **kwargs)

        # pyobs daemonizes itself and writes the PID file asynchronously — wait for it
        for _ in range(15):
            pid = self._read_pid(module)
            if pid and self._is_alive(pid):
                if self._verbose:
                    print(f"[DEBUG] {module} running with PID {pid}")
                return
            time.sleep(0.2)

        # launcher exited without confirming — show whatever it printed
        stdout, stderr = proc.communicate(timeout=2)
        print(f"Warning: {module} launched but PID not confirmed.")
        if stdout:
            print(f"  stdout: {stdout.decode(errors='replace').strip()}")  # type: ignore[attr-defined]
        if stderr:
            print(f"  stderr: {stderr.decode(errors='replace').strip()}")  # type: ignore[attr-defined]

    def _stop_service(self, module: str) -> None:
        """Stops a single module and waits for it."""
        pid = self._signal_stop(module)
        if pid is not None:
            self._wait_stopped({module: pid})

    def _signal_stop(self, module: str) -> int | None:
        """Sends SIGTERM to a module. Returns its PID, or None if it is not running (anymore)."""
        pid = self._running_pid(module)
        if pid is None:
            print(f"{module} is not running.")
            return None

        # already shutting down (e.g. an earlier "pyobsd stop" was interrupted): don't signal again, a module with
        # an older pyobs-core would get killed by a second SIGTERM in the middle of its shutdown
        if os.path.exists(self._stop_file(module)):
            print(f"{module} is already shutting down.")
            return pid

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return None
        return pid

    def _wait_stopped(self, stopping: dict[str, int]) -> None:
        """Waits for the given modules to exit and sends SIGKILL to those that take too long.

        "Too long" is stop_timeout after SIGTERM, or later if the module wrote a later deadline into its stop
        file (pyobs.utils.shutdown.extend_stop_timeout, e.g. while a camera warms up).

        The last deadline read is kept: the application removes its stop file once its shutdown is done, but the
        process lives on for a moment after that, and must not fall back to stop_timeout and get killed then."""
        default_deadline = time.time() + self._stop_timeout
        announced: dict[str, float] = {}
        last_requested: dict[str, float] = {}
        remaining = dict(stopping)

        while remaining:
            now = time.time()
            for module, pid in list(remaining.items()):
                if not self._is_alive(pid):
                    del remaining[module]
                    self._remove_run_files(module)
                    continue

                requested = read_stop_deadline(self._stop_file(module))
                if requested is not None:
                    last_requested[module] = requested
                else:
                    requested = last_requested.get(module)
                deadline = max(default_deadline, requested or 0.0)
                if requested is not None and requested > default_deadline and announced.get(module) != requested:
                    announced[module] = requested
                    print(f"{module} is shutting down, waiting up to {self._fmt_wait(requested - now)}.")

                if now >= deadline:
                    if self._verbose:
                        print(f"[DEBUG] {module} did not stop in time, sending SIGKILL")
                    else:
                        print(f"{module} did not stop in time, killing it.")
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
                    del remaining[module]
                    self._remove_run_files(module)

            if remaining:
                time.sleep(0.1)

    def _remove_run_files(self, module: str) -> None:
        """Removes PID and stop file of a module."""
        for path in (self._pid_file(module), self._stop_file(module)):
            try:
                os.remove(path)
            except OSError:
                pass


# old name, from before there were two modes
PyobsDaemon = PidFileDaemon


def main() -> None:
    # argparse.REMAINDER can't swallow a leading flag (e.g. "pyobsd logs -f")
    # unless a "--" already precedes it — insert one automatically so users
    # don't need to type it themselves.
    if "logs" in sys.argv:
        idx = sys.argv.index("logs") + 1
        if idx < len(sys.argv) and sys.argv[idx].startswith("-") and sys.argv[idx] != "--":
            sys.argv.insert(idx, "--")

    cli = PyobsDaemonCLI()
    cli()


if __name__ == "__main__":
    main()
