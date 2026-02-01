from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyobs.application import Application

from pyobs import version
from ._cli import CLI


class PyobsCLI(CLI):
    """Class for initializing and running pyobs CLI."""

    # name of section in configuration file
    CONFIG_SECTION = "pyobs"

    # list of parameters that can be defined in the config file
    GLOBAL_CONFIG_KEYS = [
        "log_level",
        "influx_log",
        "debug_time",
    ]

    def init_cli(self) -> None:
        # config
        self._parser.add_argument("config", type=str, help="Configuration file")

        # name of PID file
        self._parser.add_argument("-p", "--pid-file", type=str, default=self._config.get("pid_file", None))

        # logging
        self._parser.add_argument(
            "--log-level",
            type=str,
            choices=["critical", "error", "warning", "info", "debug"],
            default=self._config.get("log_level", "info"),
        )
        self._parser.add_argument(
            "-l", "--log-file", type=str, help="file to write log into", default=self._config.get("log_file", None)
        )
        self._parser.add_argument(
            "--influx-log",
            type=str,
            nargs=4,
            help="send to influx log: <host> <token> <org> <bucket>",
            default=self._config.get("influx_log", None),
        )

        # debug stuff
        self._parser.add_argument(
            "--debug-time",
            type=str,
            help="Fake time at start for pyobs to use",
            default=self._config.get("debug_time", None),
        )

        # version
        self._parser.add_argument("-v", "--version", action="version", version=version())

    def application(self, **kwargs: Any) -> Application:
        from pyobs.application import Application

        return Application(**kwargs)

    def run(self) -> None:
        from pyobs.utils.time import Time

        # get full path of config
        self._config["config"] = os.path.abspath(self._config["config"])

        # influx?
        if self._config["influx_log"] and isinstance(self._config["influx_log"], list):
            self._config["influx_log"] = {
                k: self._config["influx_log"][i] for i, k in enumerate(["url", "token", "org", "bucket"])
            }

        # set debug time
        if self._config["debug_time"] is not None:
            # calculate difference between now and given time
            delta = Time(self._config["debug_time"]) - Time.now()
            Time.set_offset_to_now(delta)

        # run app
        if self._config["pid_file"] is not None:
            self._start_daemon(**self._config)
        else:
            self.application(**self._config).run()

    def _start_daemon(self, pid_file: str, **kwargs: Any) -> None:
        """Start process as a daemon.

        Args:
            pid_file: Name of PID file.
        """
        import daemon
        from daemon import pidfile

        # get run directory
        run_dir = os.path.dirname(pid_file)

        # This launches the daemon in its context
        with daemon.DaemonContext(
            working_directory=run_dir, umask=0o002, pidfile=pidfile.TimeoutPIDLockFile(pid_file)
        ) as _:
            self.application(**self._config).run()


def main() -> None:
    cli = PyobsCLI()
    cli()


if __name__ == "__main__":
    main()
