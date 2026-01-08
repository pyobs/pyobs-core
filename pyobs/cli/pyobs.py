from __future__ import annotations
import argparse
import os
from typing import Type, Any, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pyobs.application import Application

from pyobs import version


def load_config(section: str) -> dict[str, Any]:
    config_file = os.path.expanduser(os.path.join("~", ".config", "pyobs.yaml"))
    if not os.path.exists(config_file):
        config_file = os.path.expanduser(os.path.join("/", "etc", "pyobs.yaml"))
        if not os.path.exists(config_file):
            return {}
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
        return {} if cfg is None else cfg[section]


def init_cli(config: dict[str, Any]) -> argparse.ArgumentParser:
    # init argument parsing
    # for all command line parameters we set the default to an environment variable,
    # so they can also be specified that way
    parser = argparse.ArgumentParser()

    # config
    parser.add_argument("config", type=str, help="Configuration file")

    # name of PID file
    parser.add_argument("-p", "--pid-file", type=str, default=config.get("pid_file", None))

    # logging
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug"],
        default=config.get("log_level", "info"),
    )
    parser.add_argument(
        "-l", "--log-file", type=str, help="file to write log into", default=config.get("log_file", None)
    )
    parser.add_argument(
        "--influx-log",
        type=str,
        nargs=4,
        help="send to influx log: <host> <token> <org> <bucket>",
        default=config.get("influx_log", None),
    )

    # debug stuff
    parser.add_argument(
        "--debug-time", type=str, help="Fake time at start for pyobs to use", default=config.get("debug_time", None)
    )

    # version
    parser.add_argument("-v", "--version", action="version", version=version())

    # return it
    return parser


def parse_cli(parser: argparse.ArgumentParser, config: dict[str, Any]) -> dict[str, Any]:
    # parse args
    args = parser.parse_args()

    # get full path of config
    if args.config:
        args.config = os.path.abspath(args.config)

    # influx?
    if args.influx_log:
        args.influx_log = {
            "url": args.influx_log[0],
            "token": args.influx_log[1],
            "org": args.influx_log[2],
            "bucket": args.influx_log[3],
        }

    # finished
    config.update(**vars(args))
    return config


def start_daemon(app_class: Type["Application"], pid_file: str, **kwargs: Any) -> None:
    """Start process as a daemon.

    Args:
        app_class: Class to create app from
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
        run(app_class, **kwargs)


def run(app_class: Type["Application"], **kwargs: Any) -> None:
    """Run a pyobs application with the given options.

    Args:
        app_class: Class to create app from
    """

    # create app and run it
    app = app_class(**kwargs)
    app.run()


def main() -> None:
    from pyobs.application import Application
    from pyobs.utils.time import Time

    # get configuration
    config = load_config("pyobs")
    parser = init_cli(config)
    config = parse_cli(parser, config)

    # set debug time
    if config["debug_time"] is not None:
        # calculate difference between now and given time
        delta = Time(config["debug_time"]) - Time.now()
        Time.set_offset_to_now(delta)

    # run app
    if config["pid_file"] is not None:
        start_daemon(app_class=Application, **config)
    else:
        run(app_class=Application, **config)


if __name__ == "__main__":
    main()
