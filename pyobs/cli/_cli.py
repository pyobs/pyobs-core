import argparse
import os
from typing import Any
import yaml


class CLI:
    # name of section in configuration file
    CONFIG_SECTION = ""

    # list of parameters that can be defined in the config file
    GLOBAL_CONFIG_KEYS: list[str] = []

    def __init__(self) -> None:
        """Initializes a new instance of the CLI class."""
        self._config: dict[str, Any] = {}
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
        config_file = os.path.expanduser(os.path.join("~", ".config", "pyobs.yaml"))
        if not os.path.exists(config_file):
            config_file = os.path.expanduser(os.path.join("/", "etc", "pyobs.yaml"))
            if not os.path.exists(config_file):
                return
        with open(config_file, "r") as f:
            cfg = yaml.safe_load(f)
            if cfg is None or self.CONFIG_SECTION not in cfg:
                return
            self._config.update(**{k: v for k, v in cfg[self.CONFIG_SECTION].items() if k in self.GLOBAL_CONFIG_KEYS})

    def _load_env(self) -> None:
        """Load config from environment variables."""
        for key in self.GLOBAL_CONFIG_KEYS:
            env_key = "PYOBS_" + key.upper()
            if env_key in os.environ:
                self._config[key] = os.environ[env_key]
