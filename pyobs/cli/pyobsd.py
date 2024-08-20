import argparse
import glob
import json
import logging
import os
import subprocess
import sys
import time
from typing import Optional, List

import yaml

log = logging.getLogger("pyobs")


class PyobsDaemon(object):
    def __init__(
        self,
        config_path: str,
        run_path: str,
        log_path: str,
        log_level: str = "info",
        chuid: Optional[str] = None,
        start_stop_daemon: str = "start-stop-daemon",
    ):
        self._config_path = config_path
        self._run_path = run_path
        self._log_path = log_path
        self._log_level = log_level
        self._chuid = chuid
        self._start_stop_daemon = start_stop_daemon

        # find pyobs executable
        filenames = [
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "pyobs"),
            "/usr/bin/pyobs",
            "/usr/local/bin/pyobs",
        ]
        for filename in filenames:
            if os.path.exists(filename):
                self._pyobs_exec = filename
                break
        # else:
        #    raise ValueError("Could not find pyobs executable.")

        # get configs and running
        self._configs = self._get_configs()
        self._running = self._get_running()

    def _get_configs(self) -> List[str]:
        # get configuration files, ignore those ending on .shared.yaml
        tmp = sorted(glob.glob(os.path.join(self._config_path, "*.yaml")))
        return list(filter(lambda t: not t.endswith(".shared.yaml"), tmp))

    def _get_running(self) -> List[str]:
        # get PID files
        pid_files = sorted(glob.glob(os.path.join(self._run_path, "*.pid")))

        # loop files
        running = []
        for pid_file in pid_files:
            # get pid
            pid = self._pid(self._module(pid_file))
            if pid is None:
                print("No PID file found.")
                continue

            # check for running
            try:
                os.kill(pid, 0)
            except OSError:
                print("Removing PID file %s without process..." % os.path.basename(pid_file))
                os.remove(pid_file)
            else:
                running.append(pid_file)

        # return running processes
        return running

    def start(self, modules: Optional[List[str]] = None) -> None:
        # get list of running processes
        running = [self._module(r) for r in self._running]
        configs = [self._module(r) for r in self._configs]

        # if no modules are given, start all
        if modules is None or len(modules) == 0:
            # ignore all configs that start with an underscore, those need to be started explicitly
            modules = [self._module(c) for c in configs if not os.path.basename(c).startswith("_")]

        # loop configs
        for module in sorted(modules):
            # exists?
            if module not in configs:
                print("module %s does not exists." % module)
                sys.exit(1)

            # start it?
            if module in running:
                print("%s already running." % module)
            else:
                print("Starting %s..." % module)
                self._start_service(module)

    def stop(self, modules: Optional[List[str]] = None) -> None:
        # if no modules are given, stop all
        if modules is None or len(modules) == 0:
            modules = [self._module(r) for r in self._running]

        # loop running and stop them
        for module in modules:
            print("Stopping %s..." % module)
            self._stop_service(module)

    def restart(self, modules: Optional[List[str]] = None) -> None:
        # stop all modules
        self.stop(modules=modules)

        # sleep a little and get running
        time.sleep(1)
        self._running = self._get_running()

        # start all modules
        self.start(modules=modules)

    def status(self, print_json: bool = False) -> None:
        # get all configs and running
        configs = [self._module(r) for r in self._configs]
        running = [self._module(r) for r in self._running]

        # if no modules are given, get all
        modules = sorted(list(set(configs + running)))

        # json or print them
        if print_json:
            print(json.dumps({m: m in running for m in modules}))
        else:
            print("cfg run module")
            for p in modules:
                print(("[X]" if p in configs else "[ ]") + " " + ("[X]" if p in running else "[ ]") + " " + p)

    def list(self) -> None:
        configs = [self._module(r) for r in self._configs]
        print("\n".join(configs))

    def _start_service(self, module: str) -> None:
        # get PID file
        pid_file = self._pid_file(module)

        # define command
        cmd = []
        cmd.extend([self._start_stop_daemon, "--start", "--quiet", "--pidfile", pid_file])

        # change user?
        if self._chuid:
            cmd.extend(["--chuid", self._chuid])

        # call to pyobs
        cmd.extend(
            [
                "--exec",
                self._pyobs_exec,
                "--",
                "--pid-file",
                pid_file,
                "--log-file",
                self._log_file(module),
                "--log-level",
                self._log_level,
                self._config_file(module),
            ]
        )

        # execute
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _stop_service(self, module: str) -> None:
        # get module name and PID
        pid_file = self._pid_file(module)

        # stop module
        cmd = [self._start_stop_daemon, "--stop", "--quiet", "--oknodo", "--pidfile", pid_file]
        if self._chuid:
            cmd.extend(["--user", self._chuid[: self._chuid.find(":")]])
        subprocess.call(cmd)

    @staticmethod
    def _module(config_file: str) -> str:
        # get basename without extension
        return os.path.splitext(os.path.basename(config_file))[0]

    def _config_file(self, module: str) -> str:
        # get pid file
        return os.path.join(self._config_path, module + ".yaml")

    def _pid_file(self, module: str) -> str:
        # get pid file
        return os.path.join(self._run_path, module + ".pid")

    def _log_file(self, module: str) -> str:
        # get pid file
        return os.path.join(self._log_path, module + ".log")

    def _pid(self, module: str) -> Optional[int]:
        # get pid file
        pid_file = self._pid_file(module)
        if not os.path.exists(pid_file):
            return None

        # get pid
        with open(pid_file, "r") as f:
            return int(f.read())


def main() -> None:
    # try to load config file
    config_filename = os.path.expanduser("~/.pyobs/pyobsd.yaml")
    config = {}
    if os.path.exists(config_filename):
        with open(config_filename, "r") as f:
            config = yaml.safe_load(f)

    # init parser
    parser = argparse.ArgumentParser(description="Daemon for pyobs")
    parser.add_argument("-p", "--path", type=str, default=config.get("path", "/opt/pyobs"))
    parser.add_argument("-c", "--config-path", type=str, default=config.get("config-path", "config"))
    parser.add_argument("-r", "--run-path", type=str, default=config.get("run-path", "run"))
    parser.add_argument("-l", "--log-path", type=str, default=config.get("log-path", "log"))
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug"],
        default=config.get("log-level", "info"),
    )
    parser.add_argument("--chuid", type=str, default=config.get("chuid", "pyobs:pyobs"))
    parser.add_argument(
        "--start-stop-daemon", type=str, default=config.get("start-stop-daemon", "/sbin/start-stop-daemon")
    )

    # commands
    sp = parser.add_subparsers(dest="command")
    sp.add_parser("start", help="start modules").add_argument("modules", type=str, nargs="*")
    sp.add_parser("stop", help="stop modules").add_argument("modules", type=str, nargs="*")
    sp.add_parser("restart", help="restart modules").add_argument("modules", type=str, nargs="*")
    sp.add_parser("status", help="status of modules").add_argument("--json", action="store_true")
    sp.add_parser("list", help="list of modules")

    # parse
    args = parser.parse_args()

    # init daemon
    daemon = PyobsDaemon(
        str(os.path.join(args.path, args.config_path)),
        str(os.path.join(args.path, args.run_path)),
        str(os.path.join(args.path, args.log_path)),
        log_level=args.log_level,
        chuid=args.chuid,
        start_stop_daemon=args.start_stop_daemon,
    )

    # run
    match args.command:
        case "start":
            daemon.start(modules=args.modules)
        case "stop":
            daemon.stop(modules=args.modules)
        case "restart":
            daemon.restart(modules=args.modules)
        case "status":
            daemon.status(print_json=args.json)
        case "list":
            daemon.list()


if __name__ == "__main__":
    main()
