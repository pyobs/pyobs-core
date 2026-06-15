from __future__ import annotations

import glob
import json
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Any

import psutil

from ._cli import CLI

log = logging.getLogger("pyobs")


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
        "chuid",
    ]

    def init_cli(self) -> None:
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
        self._parser.add_argument("--chuid", type=str, default=self._config.get("chuid", "pyobs:pyobs"))
        self._parser.add_argument("-v", "--verbose", action="store_true")

        # commands
        sp = self._parser.add_subparsers(dest="command")
        sp.add_parser("start", help="start modules").add_argument("modules", type=str, nargs="*")
        sp.add_parser("stop", help="stop modules").add_argument("modules", type=str, nargs="*")
        sp.add_parser("restart", help="restart modules").add_argument("modules", type=str, nargs="*")
        sp.add_parser("status", help="status of modules").add_argument("--json", action="store_true")
        sp.add_parser("list", help="list of modules")

    def run(self) -> None:
        # init daemon
        daemon = PyobsDaemon(
            str(os.path.join(self._config["path"], self._config["config_path"])),
            str(os.path.join(self._config["path"], self._config["run_path"])),
            str(os.path.join(self._config["path"], self._config["log_path"])),
            log_level=self._config["log_level"],
            chuid=self._config["chuid"],
            verbose=self._config["verbose"],
        )

        # run
        match self._config["command"]:
            case "start":
                daemon.start(modules=self._config["modules"])
            case "stop":
                daemon.stop(modules=self._config["modules"])
            case "restart":
                daemon.restart(modules=self._config["modules"])
            case "status":
                daemon.status(print_json=self._config["json"])
            case "list":
                daemon.list()


class PyobsDaemon:
    def __init__(
        self,
        config_path: str,
        run_path: str,
        log_path: str,
        log_level: str = "info",
        chuid: str | None = None,
        verbose: bool = False,
        **kwargs: Any,
    ):
        self._config_path = config_path
        self._run_path = run_path
        self._log_path = log_path
        self._log_level = log_level
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

    def _pid_file(self, module: str) -> str:
        return os.path.join(self._run_path, self._strip_disabled(module) + ".pid")

    def _log_file(self, module: str) -> str:
        return os.path.join(self._log_path, self._strip_disabled(module) + ".log")

    def _list_configs(self) -> list[str]:
        """Return sorted module names from *.yaml files, excluding *.shared.yaml."""
        paths = sorted(glob.glob(os.path.join(self._config_path, "*.yaml")))
        return [self._module(p) for p in paths if not p.endswith(".shared.yaml")]

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
        # stale PID file — remove it
        try:
            os.remove(self._pid_file(module))
        except OSError:
            pass
        return None

    def _process_info(self, pid: int) -> dict[str, Any]:
        """Return uptime (seconds), cpu_percent, and rss_mb for a running PID."""
        try:
            proc = psutil.Process(pid)
            uptime = time.time() - proc.create_time()
            cpu = proc.cpu_percent(interval=0.1)
            rss_mb = proc.memory_info().rss / 1024 / 1024
            return {"uptime": uptime, "cpu": cpu, "rss_mb": rss_mb}
        except psutil.NoSuchProcess:
            return {"uptime": 0.0, "cpu": 0.0, "rss_mb": 0.0}

    @staticmethod
    def _fmt_uptime(seconds: float) -> str:
        seconds = int(seconds)
        d, rem = divmod(seconds, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        if d:
            return f"{d}d {h:02d}:{m:02d}:{s:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"

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

    def stop(self, modules: list[str] | None = None) -> None:
        # if no modules given, stop all that have a live PID
        if not modules:
            modules = [m for m in self._list_configs() if self._running_pid(m) is not None]

        for module in modules:
            print(f"Stopping {module}...")
            self._stop_service(module)

    def restart(self, modules: list[str] | None = None) -> None:
        self.stop(modules=modules)
        time.sleep(1)
        self.start(modules=modules)

    def status(self, print_json: bool = False) -> None:
        configs = self._list_configs()
        # map "active" (no leading underscore) name -> config name, so that
        # PID files (always named without underscore) can be matched back to
        # their (possibly disabled) config
        active_to_config = {self._strip_disabled(m): m for m in configs}

        # also include any orphaned PID files not backed by a config
        pid_stems = [self._module(p) for p in glob.glob(os.path.join(self._run_path, "*.pid"))]
        modules = sorted(set(configs) | {active_to_config.get(s, s) for s in pid_stems})

        if print_json:
            result: dict[str, Any] = {}
            for module in modules:
                pid = self._running_pid(module)
                if pid is not None:
                    info = self._process_info(pid)
                    result[module] = {"running": True, "pid": pid, **info}
                else:
                    result[module] = {"running": False}
            print(json.dumps(result))
        else:
            # header
            print(f"{'module':<30}  {'status':<8}  {'uptime':>12}  {'cpu':>6}  {'rss':>8}")
            print("-" * 72)
            for module in modules:
                pid = self._running_pid(module)
                if pid is not None:
                    info = self._process_info(pid)
                    print(
                        f"{module:<30}  {'running':<8}  "
                        f"{self._fmt_uptime(info['uptime']):>12}  "
                        f"{info['cpu']:>5.1f}%  "
                        f"{info['rss_mb']:>6.1f} MB"
                    )
                else:
                    print(f"{module:<30}  {'stopped':<8}")

    def list(self) -> None:
        print("\n".join(self._list_configs()))

    # ── process management ────────────────────────────────────────────────────

    def _start_service(self, module: str) -> None:
        os.makedirs(self._run_path, exist_ok=True)
        os.makedirs(self._log_path, exist_ok=True)

        cmd = [
            self._pyobs_exec,
            "--pid-file",
            self._pid_file(module),
            "--log-file",
            self._log_file(module),
            "--log-level",
            self._log_level,
            self._config_file(module),
        ]

        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")

        kwargs: dict[str, Any] = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # detach from pyobsd's process group
        )
        if self._user:
            kwargs["user"] = self._user
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
            print(f"  stdout: {stdout.decode(errors='replace').strip()}")
        if stderr:
            print(f"  stderr: {stderr.decode(errors='replace').strip()}")

    def _stop_service(self, module: str) -> None:
        pid = self._running_pid(module)
        if pid is None:
            print(f"{module} is not running.")
            return

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return

        # wait up to 5 s for graceful shutdown, then SIGKILL
        for _ in range(50):
            if not self._is_alive(pid):
                break
            time.sleep(0.1)
        else:
            if self._verbose:
                print(f"[DEBUG] {module} did not stop gracefully, sending SIGKILL")
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

        # clean up PID file
        try:
            os.remove(self._pid_file(module))
        except OSError:
            pass


def main() -> None:
    cli = PyobsDaemonCLI()
    cli()


if __name__ == "__main__":
    main()
