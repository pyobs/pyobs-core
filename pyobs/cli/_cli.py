import argparse
import logging
import os
from typing import Any

import yaml

log = logging.getLogger("pyobs")

# how pyobsd runs modules: as daemons with PID files, or as systemd user units
PYOBSD_MODES = ("pid", "systemd")
PYOBSD_MODE_ENV = "PYOBSD_MODE"


def config_file_candidates() -> list[str]:
    """Where the shared pyobs config file can be, in lookup order."""
    return [
        os.path.expanduser(os.path.join("~", ".config", "pyobs.yaml")),
        os.path.join("/", "etc", "pyobs.yaml"),
        os.path.join("/", "opt", "pyobs", "storage", "pyobs.yaml"),
    ]


def find_config_file() -> str | None:
    """The shared pyobs config file, or None. The first one found wins."""
    for config_file in config_file_candidates():
        if os.path.exists(config_file):
            return config_file
    return None


def pyobsd_mode(file_config: dict[str, Any]) -> str:
    """The pyobsd mode, from $PYOBSD_MODE or else from the "pyobsd" section of the config file, "pid" by default.

    pyobs needs this too (to refuse --pid-file in systemd mode), so it does not use the CLI's own key handling.

    Args:
        file_config: Content of the config file, see CLI.file_config.

    Raises:
        ValueError: If the mode is unknown.
    """
    mode = os.environ.get(PYOBSD_MODE_ENV)
    source = "$" + PYOBSD_MODE_ENV
    if mode is None:
        section = file_config.get("pyobsd")
        mode = section.get("mode") if isinstance(section, dict) else None
        source = "pyobsd.mode in the config file"
    if mode is None:
        return "pid"
    if mode not in PYOBSD_MODES:
        raise ValueError(f"Unknown pyobsd mode {mode!r} in {source}, must be one of: {', '.join(PYOBSD_MODES)}.")
    return str(mode)


class CLI:
    # name of section in configuration file
    CONFIG_SECTION = ""

    # list of parameters that can be defined in the config file
    GLOBAL_CONFIG_KEYS: list[str] = []

    def __init__(self) -> None:
        """Initializes a new instance of the CLI class."""
        self._config: dict[str, Any] = {}
        # whole content of the config file, all sections
        self.file_config: dict[str, Any] = {}
        self._parser = argparse.ArgumentParser()

    def __call__(self) -> None:
        # load configuration file
        self._load_config()

        # environment variables
        self._load_env()

        # CLI
        self.init_cli()
        args = self._parser.parse_args()
        self._config.update(**vars(args))

        # run it
        self.run()

    def init_cli(self) -> None:
        """Overwrite this to set CLI parameters with argparse."""
        ...

    def run(self) -> None:
        """Overwrite this to actually run the CLI."""
        ...

    def _load_config(self) -> None:
        """Load config from config file"""
        config_file = find_config_file()
        if config_file is None:
            return
        log.info("Using config file %s.", config_file)
        with open(config_file) as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            return
        self.file_config = cfg
        section = cfg.get(self.CONFIG_SECTION)
        if not isinstance(section, dict):
            return
        self._config.update(**{k: v for k, v in section.items() if k in self.GLOBAL_CONFIG_KEYS})

    def _load_env(self) -> None:
        """Load config from environment variables."""
        for key in self.GLOBAL_CONFIG_KEYS:
            env_key = "PYOBS_" + key.upper()
            if env_key in os.environ:
                self._config[key] = os.environ[env_key]
